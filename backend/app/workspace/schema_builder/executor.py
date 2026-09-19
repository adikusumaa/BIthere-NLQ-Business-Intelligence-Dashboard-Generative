"""
Apply / rollback DDL against a workspace data source, and bulk insert data.
"""

import math
import os
from typing import Any, Dict, List, Optional

import pandas as pd

from app.connectors.base import BaseConnector
from app.core.logging import logger


class ExecutorError(Exception):
    """Raised when DDL or data insertion fails."""


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


def _quote_value(value: Any, sql_type: str, dialect: str) -> str:
    """Convert a Python value to a safe SQL literal."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
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


async def apply_ddl(
    connector: BaseConnector,
    ddl: str,
    drop_if_exists: bool = False,
    table_name: Optional[str] = None,
) -> bool:
    """
    Execute CREATE TABLE (and indexes).
    Optionally drop the table first.
    For PostgreSQL, uses CASCADE to handle FK dependencies.
    """
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
    batch_size: int = 1000,
) -> int:
    """
    Bulk-insert data from a file into the target table.
    Returns number of rows inserted.
    """
    df = _read_full_dataframe(file_path)
    dialect = connector.get_dialect()

    name_map = {r["original_name"]: r for r in columns_resolved}
    target_cols = [r["sql_name"] for r in columns_resolved if r["original_name"] in df.columns]
    source_cols = [r["original_name"] for r in columns_resolved if r["original_name"] in df.columns]

    if not target_cols:
        raise ExecutorError("No matching columns between file and schema")

    quoted_table = _quote_identifier(table_name, dialect)
    quoted_cols = ", ".join(_quote_identifier(c, dialect) for c in target_cols)

    inserted = 0
    total = len(df)

    for start in range(0, total, batch_size):
        chunk = df.iloc[start:start + batch_size]
        rows_sql = []
        for _, row in chunk.iterrows():
            vals = []
            for src in source_cols:
                sql_type = name_map[src]["sql_type"]
                vals.append(_quote_value(row[src], sql_type, dialect))
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
        await connector.execute_query(
            f"DROP TABLE IF EXISTS {_quote_identifier(table_name, dialect)}"
        )
        logger.info(f"[SUCCESS] Rolled back table: {table_name}")
        return True
    except Exception as exc:
        logger.error(f"[ERROR] Rollback failed: {exc}")
        raise ExecutorError(f"Rollback failed: {exc}") from exc