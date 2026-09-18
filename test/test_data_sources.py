"""
Integration tests for workspace data source registry.
Uses SQLite & DuckDB (no external DB needed).
"""

import os
import uuid
import pytest

from app.workspace import data_sources as ds_mod
from app.workspace import service as ws_service


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"DS Test {uuid.uuid4().hex[:6]}")
    yield ws
    await ws_service.delete_workspace(ws["id"], owner)


async def test_add_sqlite_data_source(workspace):
    ds = await ds_mod.add_data_source(
        workspace_id=workspace["id"],
        name="Local SQLite",
        ds_type="sqlite",
        connection=":memory:",
        is_default=True,
    )
    assert ds["type"] == "sqlite"
    assert ds["is_default"] is True

    items = await ds_mod.list_data_sources(workspace["id"])
    assert len(items) == 1
    assert items[0]["name"] == "Local SQLite"


async def test_add_duckdb_data_source(workspace):
    ds = await ds_mod.add_data_source(
        workspace_id=workspace["id"],
        name="DuckDB Workspace",
        ds_type="duckdb",
        connection=f"duckdb/test_{workspace['id']}.duckdb",
        is_default=True,
    )
    assert ds["type"] == "duckdb"


async def test_unsupported_type_rejected(workspace):
    with pytest.raises(ds_mod.UnsupportedDataSourceError):
        await ds_mod.add_data_source(
            workspace_id=workspace["id"],
            name="Oracle",
            ds_type="oracle",
            connection="x",
        )


async def test_missing_required_fields(workspace):
    with pytest.raises(ds_mod.DataSourceStoreError):
        await ds_mod.add_data_source(
            workspace_id=workspace["id"],
            name="No Path",
            ds_type="sqlite",
        )


async def test_get_workspace_connector_default(workspace):
    await ds_mod.add_data_source(
        workspace_id=workspace["id"],
        name="Default SQLite",
        ds_type="sqlite",
        connection=":memory:",
        is_default=True,
    )

    connector = await ds_mod.get_workspace_connector(workspace["id"])
    assert connector.get_dialect() == "sqlite"


async def test_test_data_source_ok(workspace):
    ds = await ds_mod.add_data_source(
        workspace_id=workspace["id"],
        name="Test SQLite",
        ds_type="sqlite",
        connection=":memory:",
        is_default=True,
    )

    ok, msg = await ds_mod.test_data_source(ds["id"])
    assert ok is True
    assert "OK" in msg

    refreshed = await ds_mod.get_data_source(ds["id"])
    assert refreshed["last_test_ok"] is True


async def test_set_default_switches(workspace):
    a = await ds_mod.add_data_source(
        workspace_id=workspace["id"], name="A", ds_type="sqlite",
        connection=":memory:", is_default=True,
    )
    b = await ds_mod.add_data_source(
        workspace_id=workspace["id"], name="B", ds_type="sqlite",
        connection=":memory:",
    )

    await ds_mod.set_default(workspace["id"], b["id"])

    refreshed_a = await ds_mod.get_data_source(a["id"])
    refreshed_b = await ds_mod.get_data_source(b["id"])
    assert refreshed_a["is_default"] is False
    assert refreshed_b["is_default"] is True


async def test_delete_data_source(workspace):
    ds = await ds_mod.add_data_source(
        workspace_id=workspace["id"], name="Delete Me",
        ds_type="sqlite", connection=":memory:", is_default=True,
    )

    await ds_mod.delete_data_source(ds["id"])

    with pytest.raises(ds_mod.DataSourceNotFoundError):
        await ds_mod.get_data_source(ds["id"])