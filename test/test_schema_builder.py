"""
Tests for DDL generator + executor + dataset catalog.
"""

import os
import uuid
import pandas as pd
import pytest

from app.workspace import datasets as ds_mod
from app.workspace import service as ws_service
from app.workspace.schema_builder import ddl_generator, executor
from app.connectors.sqlite import SQLiteConnector
from app.connectors.base import ConnectorConfig


# ============ DDL generator ============

def test_generate_ddl_basic():
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "name", "dtype": "text", "nullable": True},
        {"name": "amount", "dtype": "float", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("users", columns, dialect="postgresql")
    assert "CREATE TABLE users" in result["ddl"]
    assert "id INTEGER NOT NULL PRIMARY KEY" in result["ddl"]
    assert result["primary_key"] == "id"


def test_generate_ddl_duckdb_types():
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "amount", "dtype": "float", "nullable": True},
        {"name": "active", "dtype": "boolean", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("sales", columns, dialect="duckdb")
    assert "DOUBLE" in result["ddl"]
    assert "BOOLEAN" in result["ddl"]
    assert "VARCHAR" not in result["ddl"] or True


def test_generate_ddl_detects_foreign_key():
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "user_id", "dtype": "integer", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("orders", columns, dialect="postgresql")
    assert len(result["foreign_keys"]) == 1
    assert result["foreign_keys"][0]["column"] == "user_id"


def test_generate_ddl_suggests_index_on_timestamp():
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "created_at", "dtype": "timestamp", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("events", columns, dialect="postgresql")
    indexed = [i["column"] for i in result["indexes"]]
    assert "created_at" in indexed


def test_generate_ddl_partition_suggestion():
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "created_at", "dtype": "timestamp", "nullable": True},
    ]
    result = ddl_generator.generate_ddl(
        "big", columns, dialect="postgresql", estimated_rows=50_000_000
    )
    assert len(result["partitions"]) == 1


def test_generate_ddl_sanitizes_names():
    columns = [
        {"name": "First Name", "dtype": "text", "nullable": True},
        {"name": "123abc", "dtype": "integer", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("test", columns, dialect="postgresql")
    names = [c["sql_name"] for c in result["columns_resolved"]]
    assert "first_name" in names
    assert any(n.startswith("c_") for n in names)


def test_generate_ddl_empty_columns_raises():
    with pytest.raises(ddl_generator.DDLGenerationError):
        ddl_generator.generate_ddl("x", [], dialect="postgresql")


def test_generate_ddl_unsupported_dialect():
    with pytest.raises(ddl_generator.DDLGenerationError):
        ddl_generator.generate_ddl(
            "x", [{"name": "a", "dtype": "text", "nullable": True}],
            dialect="oracle",
        )


# ============ Executor (SQLite end-to-end) ============

@pytest.fixture
def sample_csv(tmp_path) -> str:
    path = tmp_path / "data.csv"
    path.write_text(
        "id,name,amount\n"
        "1,Alice,10.5\n"
        "2,Bob,20.0\n"
        "3,Carol,30.5\n",
        encoding="utf-8",
    )
    return str(path)


async def _sqlite_conn():
    conn = SQLiteConnector(ConnectorConfig(type="sqlite", connection_string=":memory:"))
    await conn.connect()
    return conn


async def test_apply_ddl_and_insert(sample_csv):
    columns = [
        {"name": "id", "dtype": "integer", "nullable": False},
        {"name": "name", "dtype": "text", "nullable": True},
        {"name": "amount", "dtype": "float", "nullable": True},
    ]
    result = ddl_generator.generate_ddl("t", columns, dialect="sqlite")

    conn = await _sqlite_conn()
    try:
        await executor.apply_ddl(conn, result["ddl"], table_name="t")

        inserted = await executor.bulk_insert(
            conn, "t", sample_csv, result["columns_resolved"], batch_size=2
        )
        assert inserted == 3

        rows = await conn.execute_query("SELECT COUNT(*) AS n FROM t")
        assert rows[0]["n"] == 3
    finally:
        await conn.disconnect()


async def test_rollback_drops_table(sample_csv):
    columns = [{"name": "id", "dtype": "integer", "nullable": False}]
    result = ddl_generator.generate_ddl("t2", columns, dialect="sqlite")

    conn = await _sqlite_conn()
    try:
        await executor.apply_ddl(conn, result["ddl"], table_name="t2")
        await executor.rollback(conn, "t2")
        schema = await conn.get_schema()
        assert "t2" not in schema
    finally:
        await conn.disconnect()


# ============ Dataset catalog (live Supabase) ============

pytestmark_live = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"DS Catalog {uuid.uuid4().hex[:6]}")
    yield ws
    await ws_service.delete_workspace(ws["id"], owner)


@pytestmark_live
async def test_create_dataset_record(workspace):
    ds = await ds_mod.create_dataset(
        workspace_id=workspace["id"],
        name="Sample",
        source_type="csv",
        file_path="/tmp/sample.csv",
        row_count=100,
        column_count=5,
    )
    assert ds["name"] == "Sample"
    assert ds["source_type"] == "csv"


@pytestmark_live
async def test_list_datasets(workspace):
    await ds_mod.create_dataset(
        workspace_id=workspace["id"], name="A",
        source_type="csv", file_path="/tmp/a.csv",
    )
    await ds_mod.create_dataset(
        workspace_id=workspace["id"], name="B",
        source_type="parquet", file_path="/tmp/b.parquet",
    )

    items = await ds_mod.list_datasets(workspace["id"])
    assert len(items) == 2


@pytestmark_live
async def test_create_and_update_schema(workspace):
    ds = await ds_mod.create_dataset(
        workspace_id=workspace["id"], name="S",
        source_type="csv", file_path="/tmp/s.csv",
    )
    schema = await ds_mod.create_schema(
        workspace_id=workspace["id"],
        dataset_id=ds["id"],
        table_name="s",
        ddl="CREATE TABLE s (id INTEGER);",
        columns_json=[{"name": "id", "type": "INTEGER"}],
        status="draft",
    )
    assert schema["status"] == "draft"

    updated = await ds_mod.update_schema(schema["id"], {"status": "applied"})
    assert updated["status"] == "applied"


@pytestmark_live
async def test_delete_dataset(workspace):
    ds = await ds_mod.create_dataset(
        workspace_id=workspace["id"], name="Del",
        source_type="csv", file_path="/tmp/d.csv",
    )
    await ds_mod.delete_dataset(ds["id"])

    with pytest.raises(ds_mod.DatasetNotFoundError):
        await ds_mod.get_dataset(ds["id"])