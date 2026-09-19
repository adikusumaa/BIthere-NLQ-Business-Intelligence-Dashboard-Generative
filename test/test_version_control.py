"""
Tests for conflict detector, lock, version control diff/rollback,
and undo/redo stack.
"""

import os
import uuid
import pytest

from app.dashboard import state_store
from app.dashboard.conflict_detector import ConflictError, check_conflict
from app.dashboard.lock import LockError, lock
from app.dashboard.patch_model import ChangeColorPatch, RemoveCardPatch
from app.dashboard.state_model import (
    Card,
    DashboardState,
    Page,
    Position,
)
from app.dashboard import version_control
from app.dashboard import undo_redo
from app.workspace import service as ws_service


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


def _state(dashboard_id, workspace_id, version=1, parent=None, title="A", color=None) -> DashboardState:
    style = {"color": color} if color else {}
    return DashboardState(
        dashboard_id=dashboard_id,
        workspace_id=workspace_id,
        version=version,
        parent_version=parent,
        pages=[
            Page(
                id="p1", name="P",
                cards=[
                    Card(
                        id="c-a", title=title, type="bar",
                        position=Position(row=0, col=0),
                        style=style,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"VC Test {uuid.uuid4().hex[:6]}")
    yield ws
    await ws_service.delete_workspace(ws["id"], owner)


# =====================================================
# Conflict detector
# =====================================================

async def test_no_conflict(workspace):
    dashboard_id = str(uuid.uuid4())
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1))
    version = await check_conflict(dashboard_id, base_version=1)
    assert version == 1


async def test_conflict_raises(workspace):
    dashboard_id = str(uuid.uuid4())
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1))
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=2, parent=1))

    with pytest.raises(ConflictError):
        await check_conflict(dashboard_id, base_version=1)


# =====================================================
# Lock
# =====================================================

async def test_lock_acquire_and_release():
    async with lock("test-dash-lock"):
        pass

    # Second lock should succeed after release
    async with lock("test-dash-lock"):
        pass


async def test_lock_conflict():
    async with lock("test-lock-conflict"):
        with pytest.raises(LockError):
            async with lock("test-lock-conflict"):
                pass


# =====================================================
# Version control
# =====================================================

async def test_diff_states():
    a = _state("d", "w", version=1, title="A")
    b = _state("d", "w", version=2, parent=1, title="B")
    diff = version_control.diff_states(a, b)
    assert diff["from_version"] == 1
    assert diff["to_version"] == 2
    assert any(m["field"] == "title" for m in diff["modified"])


async def test_rollback_creates_new_version(workspace):
    dashboard_id = str(uuid.uuid4())
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=1, title="v1"))
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=2, parent=1, title="v2"))
    await state_store.save_version(dashboard_id, _state(dashboard_id, workspace["id"], version=3, parent=2, title="v3"))

    new_state = await version_control.rollback(dashboard_id, target_version=1)

    assert new_state.version == 4  # version increments
    assert new_state.parent_version == 3
    # Content equals v1 (title "v1")
    assert new_state.pages[0].cards[0].title == "v1"

    # Check patch log has rollback record
    patches = await state_store.get_patches(dashboard_id)
    assert any(p["patch_json"].get("patch_type") == "ROLLBACK_TO_VERSION" for p in patches)


# =====================================================
# Undo/Redo
# =====================================================

async def test_undo_redo_stack():
    sid = f"test-{uuid.uuid4().hex[:8]}"

    patch = ChangeColorPatch(card_id="c-a", color="#000000")
    await undo_redo.push_undo(sid, patch)

    popped = await undo_redo.undo(sid)
    assert popped is not None
    assert popped["patch_type"] == "CHANGE_COLOR"

    redone = await undo_redo.redo(sid)
    assert redone is not None
    assert redone["patch_type"] == "CHANGE_COLOR"

    await undo_redo.clear_stack(sid)


async def test_undo_empty_returns_none():
    sid = f"test-{uuid.uuid4().hex[:8]}"
    assert await undo_redo.undo(sid) is None


async def test_push_undo_clears_redo():
    sid = f"test-{uuid.uuid4().hex[:8]}"
    p1 = ChangeColorPatch(card_id="c-a", color="#111111")
    p2 = ChangeColorPatch(card_id="c-a", color="#222222")

    await undo_redo.push_undo(sid, p1)
    await undo_redo.undo(sid)  # moves p1 to redo

    # Now push new action — redo should be cleared
    await undo_redo.push_undo(sid, p2)

    assert await undo_redo.redo(sid) is None

    await undo_redo.clear_stack(sid)