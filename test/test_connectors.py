"""
Integration tests for connector factory + SQLite + DuckDB (no external DB needed).
"""

import os
import uuid
import pytest

from app.connectors import (
    build_connector,
    get_connector,
    CONNECTOR_REGISTRY,
)
from app.connectors.base import ConnectorConfig
from app.connectors.sqlite import SQLiteConnector
from app.connectors.duckdb import DuckDBConnector


# --- Registry & factory ---

def test_registry_contains_all_v2_types():
    assert "postgres" in CONNECTOR_REGISTRY
    assert "postgresql" in CONNECTOR_REGISTRY
    assert "mysql" in CONNECTOR_REGISTRY
    assert "mongodb" in CONNECTOR_REGISTRY
    assert "sqlite" in CONNECTOR_REGISTRY
    assert "duckdb" in CONNECTOR_REGISTRY


def test_build_connector_unknown_type():
    with pytest.raises(ValueError):
        build_connector(ConnectorConfig(type="oracle"))


def test_build_connector_returns_instance():
    cfg = ConnectorConfig(type="sqlite", connection_string=":memory:")
    conn = build_connector(cfg)
    assert isinstance(conn, SQLiteConnector)


def test_supports_sql_flags():
    sqlite_cfg = ConnectorConfig(type="sqlite", connection_string=":memory:")
    assert build_connector(sqlite_cfg).supports_sql() is True

    mongo_cfg = ConnectorConfig(type="mongodb", connection_string="mongodb://x")
    assert build_connector(mongo_cfg).supports_sql() is False


def test_get_dialect_per_connector():
    assert build_connector(ConnectorConfig(type="sqlite", connection_string=":memory:")).get_dialect() == "sqlite"
    assert build_connector(ConnectorConfig(type="duckdb", database=":memory:")).get_dialect() == "duckdb"
    assert build_connector(ConnectorConfig(type="mongodb", connection_string="mongodb://x")).get_dialect() == "mongodb"


# --- SQLite end-to-end ---

async def test_sqlite_create_and_query():
    conn = SQLiteConnector(ConnectorConfig(type="sqlite", connection_string=":memory:"))
    await conn.connect()
    try:
        await conn.execute_query("CREATE TABLE t (id INTEGER, name TEXT)")
        await conn.execute_query("INSERT INTO t VALUES (1, 'a'), (2, 'b')")
        rows = await conn.execute_query("SELECT * FROM t ORDER BY id")
        assert len(rows) == 2
        assert rows[0]["name"] == "a"
        assert rows[1]["name"] == "b"
    finally:
        await conn.disconnect()


async def test_sqlite_get_schema():
    conn = SQLiteConnector(ConnectorConfig(type="sqlite", connection_string=":memory:"))
    await conn.connect()
    try:
        await conn.execute_query("CREATE TABLE users (id INTEGER, email TEXT)")
        schema = await conn.get_schema()
        assert "users" in schema
        cols = {c["column"] for c in schema["users"]}
        assert {"id", "email"} <= cols
    finally:
        await conn.disconnect()


# --- DuckDB end-to-end (per-workspace file) ---

async def test_duckdb_create_and_query(tmp_path, monkeypatch):
    monkeypatch.setattr("app.connectors.duckdb.settings.DUCKDB_DIR", str(tmp_path))

    ws_id = str(uuid.uuid4())
    cfg = ConnectorConfig(type="duckdb", options={"workspace_id": ws_id})
    conn = DuckDBConnector(cfg)
    await conn.connect()
    try:
        await conn.execute_query("CREATE TABLE t (id INTEGER, v DOUBLE)")
        await conn.execute_query("INSERT INTO t VALUES (1, 1.5), (2, 2.5)")
        rows = await conn.execute_query("SELECT COUNT(*) AS n, SUM(v) AS total FROM t")
        assert rows[0]["n"] == 2
        assert float(rows[0]["total"]) == 4.0
    finally:
        await conn.disconnect()

    db_file = os.path.join(str(tmp_path), f"{ws_id}.duckdb")
    assert os.path.exists(db_file)


async def test_duckdb_get_schema(tmp_path, monkeypatch):
    monkeypatch.setattr("app.connectors.duckdb.settings.DUCKDB_DIR", str(tmp_path))

    cfg = ConnectorConfig(type="duckdb", options={"workspace_id": str(uuid.uuid4())})
    conn = DuckDBConnector(cfg)
    await conn.connect()
    try:
        await conn.execute_query("CREATE TABLE sales (id INTEGER, amount DOUBLE)")
        schema = await conn.get_schema()
        assert "sales" in schema
        cols = {c["column"] for c in schema["sales"]}
        assert {"id", "amount"} <= cols
    finally:
        await conn.disconnect()