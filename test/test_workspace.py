"""
Integration tests for workspace CRUD service (hits real Supabase).
"""

import os
import uuid
import pytest

from app.workspace import service as ws_service
from app.workspace.service import (
    WorkspaceNotFoundError,
    WorkspaceAccessError,
    WorkspaceStoreError,
    MemberNotFoundError,
)


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


def _uuid() -> str:
    return str(uuid.uuid4())


async def test_create_and_get_workspace():
    owner = _uuid()
    name = f"Test WS {uuid.uuid4().hex[:6]}"

    ws = await ws_service.create_workspace(owner, name)
    assert ws["name"] == name
    assert ws["owner_id"] == owner
    assert ws["slug"]

    fetched = await ws_service.get_workspace(ws["id"])
    assert fetched["id"] == ws["id"]

    await ws_service.delete_workspace(ws["id"], owner)


async def test_get_workspace_not_found():
    with pytest.raises(WorkspaceNotFoundError):
        await ws_service.get_workspace(_uuid())


async def test_creator_is_owner():
    owner = _uuid()
    ws = await ws_service.create_workspace(owner, f"Owner Test {uuid.uuid4().hex[:6]}")

    members = await ws_service.list_members(ws["id"])
    assert len(members) == 1
    assert members[0]["user_id"] == owner
    assert members[0]["role"] == "owner"

    await ws_service.delete_workspace(ws["id"], owner)


async def test_list_user_workspaces():
    owner = _uuid()
    name = f"List WS {uuid.uuid4().hex[:6]}"
    ws = await ws_service.create_workspace(owner, name)

    workspaces = await ws_service.list_user_workspaces(owner)
    ids = [w["id"] for w in workspaces]
    assert ws["id"] in ids

    await ws_service.delete_workspace(ws["id"], owner)


async def test_add_and_update_member():
    owner = _uuid()
    member = _uuid()
    ws = await ws_service.create_workspace(owner, f"Member Test {uuid.uuid4().hex[:6]}")

    await ws_service.add_member(ws["id"], member, "analyst")
    members = await ws_service.list_members(ws["id"])
    assert any(m["user_id"] == member and m["role"] == "analyst" for m in members)

    await ws_service.update_role(ws["id"], member, "admin")
    members = await ws_service.list_members(ws["id"])
    assert any(m["user_id"] == member and m["role"] == "admin" for m in members)

    await ws_service.delete_workspace(ws["id"], owner)


async def test_remove_member():
    owner = _uuid()
    member = _uuid()
    ws = await ws_service.create_workspace(owner, f"Remove Test {uuid.uuid4().hex[:6]}")

    await ws_service.add_member(ws["id"], member, "viewer")
    await ws_service.remove_member(ws["id"], member)

    members = await ws_service.list_members(ws["id"])
    assert not any(m["user_id"] == member for m in members)

    await ws_service.delete_workspace(ws["id"], owner)


async def test_update_role_member_not_found():
    owner = _uuid()
    ws = await ws_service.create_workspace(owner, f"NotFound Test {uuid.uuid4().hex[:6]}")

    with pytest.raises(MemberNotFoundError):
        await ws_service.update_role(ws["id"], _uuid(), "admin")

    await ws_service.delete_workspace(ws["id"], owner)


async def test_delete_workspace_requires_owner():
    owner = _uuid()
    other = _uuid()
    ws = await ws_service.create_workspace(owner, f"Access Test {uuid.uuid4().hex[:6]}")

    with pytest.raises(WorkspaceAccessError):
        await ws_service.delete_workspace(ws["id"], other)

    await ws_service.delete_workspace(ws["id"], owner)


async def test_invalid_role_rejected():
    owner = _uuid()
    ws = await ws_service.create_workspace(owner, f"Role Test {uuid.uuid4().hex[:6]}")

    with pytest.raises(WorkspaceAccessError):
        await ws_service.add_member(ws["id"], _uuid(), "superadmin")

    await ws_service.delete_workspace(ws["id"], owner)