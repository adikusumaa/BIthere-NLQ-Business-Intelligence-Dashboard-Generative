"""
Integration tests for dashboard state store (hits Supabase).
"""

import os
import uuid
import pytest

from app.dashboard.state_model import (
    Card,
    DashboardState,
    Page,
    Position,
)
from app.dashboard import state_store as store
from app.dashboard.patch_model import RemoveCardPatch
from app.workspace import service as ws_service


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


def _state(dashboard_id: str, workspace_id: str, version: int = 1, parent=None) -> DashboardState:
    return DashboardState(
        dashboard_id=dashboard_id,
        workspace_id=workspace_id,
        version=version,
        parent_version=parent,
        pages=[
            Page(
                id="page-1",
                name="Overview",
                cards=[
                    Card(id="card-a", title="A", type="scalar", position=Position(row=0, col=0)),
                ],
            ),
        ],
    )


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"Store Test {uuid.uuid4().hex[:6]}")
    yield ws
    await ws_service.delete_workspace(ws["id"], owner)


async def test_save_and_load_version(workspace):
    dashboard_id = str(uuid.uuid4())
    state = _state(dashboard_id, workspace["id"], version=1)

    await store.save_version(dashboard_id, state, patch=None, user_id=None)

    loaded = await store.load_version(dashboard_id, 1)
    assert loaded.version == 1
    assert loaded.pages[0].cards[0].id == "card-a"


async def test_load_latest(workspace):
    dashboard_id = str(uuid.uuid4())
    await store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1))
    await store.save_version(
        dashboard_id, _state(dashboard_id, workspace["id"], version=2, parent=1)
    )

    latest = await store.load_latest(dashboard_id)
    assert latest.version == 2


async def test_list_versions(workspace):
    dashboard_id = str(uuid.uuid4())
    for v in (1, 2, 3):
        await store.save_version(
            dashboard_id, _state(dashboard_id, workspace["id"], version=v, parent=v - 1 if v > 1 else None)
        )

    versions = await store.list_versions(dashboard_id)
    assert len(versions) == 3
    assert versions[0]["version"] == 3  # newest first


async def test_save_with_patch_records_log(workspace):
    dashboard_id = str(uuid.uuid4())
    await store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1))

    patch = RemoveCardPatch(card_id="card-a")
    await store.save_version(
        dashboard_id,
        _state(dashboard_id, workspace["id"], version=2, parent=1),
        patch=patch,
        from_version=1,
    )

    patches = await store.get_patches(dashboard_id)
    assert len(patches) == 1
    assert patches[0]["from_version"] == 1
    assert patches[0]["to_version"] == 2
    assert patches[0]["status"] == "applied"


async def test_load_missing_raises(workspace):
    with pytest.raises(store.DashboardNotFoundError):
        await store.load_version(str(uuid.uuid4()), 1)


async def test_delete_dashboard(workspace):
    dashboard_id = str(uuid.uuid4())
    await store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1))

    await store.delete_dashboard(dashboard_id)

    with pytest.raises(store.DashboardNotFoundError):
        await store.load_latest(dashboard_id)