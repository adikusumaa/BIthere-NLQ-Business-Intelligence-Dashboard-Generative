"""
Apply / rollback DDL against a workspace data source, and bulk insert data.
Fast path uses PostgreSQL COPY protocol via asyncpg.copy_records_to_table().

Robust preprocessing:
  - auto-detects numeric/currency columns from actual data
  - auto-detects timestamp columns and converts strings
  - converts NaN / NaT / pd.NaT to Python None (vectorized)
  - localizes tz-naive timestamps to UTC
  - does NOT depend on frontend-supplied dtype
"""

import math
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from app.connectors.base import BaseConnector
from app.core.logging import logger


class ExecutorError(Exception):
    """Raised when DDL or data insertion fails."""


CURRENCY_STRIP = re.compile(r"[$,€£¥\s]")
NULL_LITERALS = {"", "nan", "None", "NaN", "null", "NULL", "<NA>", "NaT"}


def _read_full_dataframe(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        from app.workspace.dataset_parser import detect_encoding, sniff_delimiter
        enc = detect_encoding(file_path)
        sep = sniff_delimiter(file_path, enc)
        return pd.read_csv(file_path, encoding=enc, sep=sep, low_memory=False)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    if ext == ".parquet":
        return pd.read_parquet(file_path)
    raise ExecutorError(f"Unsupported file: {ext}")


def _quote_value(value: Any, dtype: str, dialect: str) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float) and math.isnan(value):
        return "NULL"
    if isinstance(value, bool):
        if dialect == "sqlite":
            return "1" if value else "0"
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return f"'{value.isoformat()}'"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _quote_identifier(name: str, dialect: str) -> str:
    if dialect == "mysql":
        return f"`{name}`"
    return f'"{name}"'


def _looks_numeric(sample: pd.Series) -> bool:
    """Return True if the sample can be parsed as numeric."""
    if len(sample) == 0:
        return False
    s = sample.dropna().astype(str).head(30)
    if len(s) == 0:
        return False
    cleaned = s.str.replace(CURRENCY_STRIP, "", regex=True)
    try:
        [float(c) for c in cleaned]
        return True
    except (ValueError, TypeError):
        return False


def _looks_timestamp(sample: pd.Series) -> bool:
    """Return True if the sample looks like ISO 8601 timestamp."""
    if len(sample) == 0:
        return False
    s = sample.dropna().astype(str).head(30)
    if len(s) == 0:
        return False
    iso = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?")
    if not all(iso.match(v) for v in s):
        return False
    try:
        pd.to_datetime(s, errors="raise")
        return True
    except Exception:
        return False


def _preprocess_dataframe(
    df: pd.DataFrame,
    source_cols: List[str],
    type_by_src: Dict[str, str],
) -> pd.DataFrame:
    """
    Normalize values before insert:
      1. Numeric columns -> strip $, , and coerce to numeric
      2. Timestamp columns -> parse to pd.Timestamp
      3. Everything else stays as-is
    """
    sub = df[source_cols].copy()

    for col in source_cols:
        hint = type_by_src.get(col, "text").lower()

        # --- Numeric columns ---
        is_numeric_hint = hint in ("float", "integer", "bigint")
        if is_numeric_hint or _looks_numeric(sub[col]):
            cleaned = (
                sub[col]
                .astype(str)
                .str.replace(CURRENCY_STRIP, "", regex=True)
                .replace({k: None for k in NULL_LITERALS})
            )
            sub[col] = pd.to_numeric(cleaned, errors="coerce")
            continue

        # --- Timestamp columns ---
        if hint == "timestamp" or _looks_timestamp(sub[col]):
            sub[col] = pd.to_datetime(sub[col], errors="coerce")
            continue

    return sub


def _to_records(df_clean: pd.DataFrame, target_cols: List[str]) -> List[tuple]:
    """
    Convert DataFrame to list of tuples.
      - NaN / NaT -> None
      - tz-naive pd.Timestamp -> UTC-localized Python datetime
      - other values stay native
    """
    normalized = df_clean[target_cols].astype(object).where(
        pd.notna(df_clean[target_cols]), None
    )

    records: List[tuple] = []
    for row in normalized.itertuples(index=False, name=None):
        cleaned: List[Any] = []
        for v in row:
            if isinstance(v, pd.Timestamp):
                if v.tz is None:
                    v = v.tz_localize("UTC")
                cleaned.append(v.to_pydatetime())
            else:
                cleaned.append(v)
        records.append(tuple(cleaned))
    return records


async def apply_ddl(
    connector: BaseConnector,
    ddl: str,
    drop_if_exists: bool = False,
    table_name: Optional[str] = None,
) -> bool:
    """Execute CREATE TABLE (and indexes). Drops first if requested."""
    try:
        if drop_if_exists and table_name:
            dialect = connector.get_dialect()
            quoted = _quote_identifier(table_name, dialect)
            if dialect == "postgresql":
                await connector.execute_query(f"DROP TABLE IF EXISTS {quoted} CASCADE")
            else:
                await connector.execute_query(f"DROP TABLE IF EXISTS {quoted}")

        statements = [s.strip() for s in ddl.split(";") if s.strip()]
        for stmt in statements:
            await connector.execute_query(stmt)

        logger.info(f"[SUCCESS] DDL applied ({len(statements)} statements)")
        return True
    except Exception as exc:
        logger.error(f"[ERROR] DDL apply failed: {exc}")
        raise ExecutorError(f"DDL apply failed: {exc}") from exc


async def bulk_insert(
    connector: BaseConnector,
    table_name: str,
    file_path: str,
    columns_resolved: List[Dict[str, Any]],
    batch_size: int = 5000,
) -> int:
    """
    Bulk-insert data from file into table.

    Strategy:
      - PostgreSQL + asyncpg pool -> COPY protocol (fast)
      - Otherwise -> INSERT VALUES batch (portable)
    """
    df = _read_full_dataframe(file_path)
    dialect = connector.get_dialect()

    target_cols: List[str] = []
    source_cols: List[str] = []
    type_by_src: Dict[str, str] = {}

    for r in columns_resolved:
        if r["original_name"] in df.columns:
            target_cols.append(r["sql_name"])
            source_cols.append(r["original_name"])
            type_by_src[r["original_name"]] = r.get("dtype", "text")

    if not target_cols:
        raise ExecutorError("No matching columns between file and schema")

    df_clean = _preprocess_dataframe(df, source_cols, type_by_src)

    total = len(df_clean)
    logger.info(
        f"[PROCESS] Bulk insert starting: {total} rows into {table_name} ({dialect})"
    )

    # PostgreSQL COPY fast path
    if dialect == "postgresql" and hasattr(connector, "pool") and connector.pool:
        try:
            return await _copy_postgres(connector, table_name, df_clean, target_cols)
        except Exception as exc:
            logger.warning(f"[WARNING] COPY path failed, falling back to INSERT: {exc}")

    return await _insert_values(connector, table_name, df_clean, target_cols, batch_size)


async def _copy_postgres(
    connector: BaseConnector,
    table_name: str,
    df_clean: pd.DataFrame,
    target_cols: List[str],
) -> int:
    """Fast path: asyncpg.copy_records_to_table()."""
    records = _to_records(df_clean, target_cols)

    async with connector.pool.acquire() as connection:
        await connection.copy_records_to_table(
            table_name,
            records=records,
            columns=target_cols,
        )

    logger.info(f"[SUCCESS] COPY insert complete: {len(records)} rows into {table_name}")
    return len(records)


async def _insert_values(
    connector: BaseConnector,
    table_name: str,
    df_clean: pd.DataFrame,
    target_cols: List[str],
    batch_size: int,
) -> int:
    """Generic INSERT VALUES path (fallback for COPY failure or non-Postgres)."""
    dialect = connector.get_dialect()
    quoted_table = _quote_identifier(table_name, dialect)
    quoted_cols = ", ".join(_quote_identifier(c, dialect) for c in target_cols)

    records = _to_records(df_clean, target_cols)
    total = len(records)
    inserted = 0

    for start in range(0, total, batch_size):
        chunk = records[start:start + batch_size]
        rows_sql = []
        for row in chunk:
            vals = [_quote_value(v, "text", dialect) for v in row]
            rows_sql.append("(" + ", ".join(vals) + ")")

        if not rows_sql:
            continue

        stmt = f"INSERT INTO {quoted_table} ({quoted_cols}) VALUES " + ", ".join(rows_sql)

        try:
            await connector.execute_query(stmt)
            inserted += len(rows_sql)
            logger.info(f"[PROCESS] Inserted batch: {inserted}/{total}")
        except Exception as exc:
            logger.error(f"[ERROR] Insert failed at row {start}: {exc}")
            raise ExecutorError(f"Insert failed at row {start}: {exc}") from exc

    logger.info(f"[SUCCESS] Bulk insert complete: {inserted} rows into {table_name}")
    return inserted


async def rollback(connector: BaseConnector, table_name: str) -> bool:
    """Drop the table to undo an applied schema."""
    dialect = connector.get_dialect()
    try:
        quoted = _quote_identifier(table_name, dialect)
        if dialect == "postgresql":
            await connector.execute_query(f"DROP TABLE IF EXISTS {quoted} CASCADE")
        else:
            await connector.execute_query(f"DROP TABLE IF EXISTS {quoted}")
        logger.info(f"[SUCCESS] Rolled back table: {table_name}")
        return True
    except Exception as exc:
        logger.error(f"[ERROR] Rollback failed: {exc}")
        raise ExecutorError(f"Rollback failed: {exc}") from exc