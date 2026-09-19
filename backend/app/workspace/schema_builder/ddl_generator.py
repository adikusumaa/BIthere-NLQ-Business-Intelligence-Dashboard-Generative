"""
Auto-generate DDL (CREATE TABLE) from inferred column types.
Suggests primary key, foreign keys, indexes, and partitions.
"""

import re
from typing import Any, Dict, List, Optional


# Map inferred types to SQL types for each dialect
TYPE_MAP = {
    "postgresql": {
        "integer": "INTEGER",
        "float": "NUMERIC",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMPTZ",
        "text": "TEXT",
    },
    "duckdb": {
        "integer": "INTEGER",
        "float": "DOUBLE",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "text": "VARCHAR",
    },
    "mysql": {
        "integer": "INT",
        "float": "DECIMAL(18,4)",
        "boolean": "TINYINT(1)",
        "timestamp": "DATETIME",
        "text": "TEXT",
    },
    "sqlite": {
        "integer": "INTEGER",
        "float": "REAL",
        "boolean": "INTEGER",
        "timestamp": "TEXT",
        "text": "TEXT",
    },
}


PK_NAME_PATTERNS = [r"^id$", r".*_id$", r"^.*_key$"]
FK_NAME_PATTERN = re.compile(r"^(.+)_id$")


class DDLGenerationError(Exception):
    """Raised when DDL cannot be generated."""


def _sanitize_identifier(name: str) -> str:
    """Convert arbitrary column names into safe SQL identifiers."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower())
    if not clean:
        clean = "col"
    if clean[0].isdigit():
        clean = f"c_{clean}"
    return clean


def _detect_primary_key(columns: List[Dict[str, Any]]) -> Optional[str]:
    """Heuristic: first integer column named 'id' or ending with '_id'."""
    for col in columns:
        name = col["name"].lower()
        if col["dtype"] == "integer" and any(
            re.match(p, name) for p in PK_NAME_PATTERNS
        ):
            return col["name"]
    for col in columns:
        if col["name"].lower() == "id":
            return col["name"]
    return None


def _detect_foreign_keys(columns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Suggest FKs based on `{table}_id` naming convention."""
    fks = []
    for col in columns:
        name = col["name"].lower()
        match = FK_NAME_PATTERN.match(name)
        if match and name != "id":
            target = match.group(1)
            fks.append({"column": col["name"], "references_table": f"{target}s", "references_column": "id"})
    return fks


def _suggest_indexes(
    columns: List[Dict[str, Any]], foreign_keys: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Suggest indexes on FK columns and timestamp/date columns."""
    indexes = []
    fk_cols = {fk["column"] for fk in foreign_keys}
    for col in columns:
        name = col["name"].lower()
        if col["name"] in fk_cols:
            indexes.append({"column": col["name"], "reason": "foreign key"})
        elif col["dtype"] == "timestamp" or name in ("date", "created_at", "updated_at"):
            indexes.append({"column": col["name"], "reason": "time filter"})
    return indexes


def _suggest_partitions(
    columns: List[Dict[str, Any]], estimated_rows: int
) -> List[Dict[str, str]]:
    """Suggest partitioning for large tables (> 10M rows)."""
    if estimated_rows <= 10_000_000:
        return []
    for col in columns:
        if col["dtype"] == "timestamp":
            return [{"column": col["name"], "strategy": "range", "interval": "monthly"}]
    return []


def generate_ddl(
    table_name: str,
    columns: List[Dict[str, Any]],
    dialect: str = "postgresql",
    estimated_rows: int = 0,
    primary_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a CREATE TABLE statement plus schema suggestions.

    Args:
        table_name: Target table name.
        columns: List of {name, dtype, nullable}.
        dialect: postgresql | duckdb | mysql | sqlite.
        estimated_rows: Used for partition suggestions.
        primary_key: Override detected PK.

    Returns:
        dict with ddl, columns_resolved, primary_key, foreign_keys,
        indexes, partitions.
    """
    if not columns:
        raise DDLGenerationError("No columns provided")

    type_map = TYPE_MAP.get(dialect)
    if not type_map:
        raise DDLGenerationError(f"Unsupported dialect: {dialect}")

    safe_table = _sanitize_identifier(table_name)
    resolved = []
    used_names = set()

    for col in columns:
        safe_name = _sanitize_identifier(col["name"])
        base = safe_name
        i = 2
        while safe_name in used_names:
            safe_name = f"{base}_{i}"
            i += 1
        used_names.add(safe_name)

        sql_type = type_map.get(col["dtype"], type_map["text"])
        nullable = col.get("nullable", True)
        resolved.append({
            "original_name": col["name"],
            "sql_name": safe_name,
            "sql_type": sql_type,
            "nullable": nullable,
            "dtype": col["dtype"],
        })

    pk = primary_key or _detect_primary_key(columns)
    pk_sql_name = None
    if pk:
        for r in resolved:
            if r["original_name"] == pk:
                pk_sql_name = r["sql_name"]
                break

    fks = _detect_foreign_keys(columns)
    indexes = _suggest_indexes(columns, fks)
    partitions = _suggest_partitions(columns, estimated_rows)

    lines = []
    for r in resolved:
        null_clause = "" if r["nullable"] else " NOT NULL"
        pk_clause = " PRIMARY KEY" if r["sql_name"] == pk_sql_name else ""
        lines.append(f"    {r['sql_name']} {r['sql_type']}{null_clause}{pk_clause}")

    ddl = f"CREATE TABLE {safe_table} (\n" + ",\n".join(lines) + "\n);"

    for idx in indexes:
        idx_col = next((r["sql_name"] for r in resolved if r["original_name"] == idx["column"]), None)
        if idx_col:
            ddl += f"\nCREATE INDEX idx_{safe_table}_{idx_col} ON {safe_table} ({idx_col});"

    return {
        "table_name": safe_table,
        "dialect": dialect,
        "ddl": ddl,
        "columns_resolved": resolved,
        "primary_key": pk,
        "foreign_keys": fks,
        "indexes": indexes,
        "partitions": partitions,
    }