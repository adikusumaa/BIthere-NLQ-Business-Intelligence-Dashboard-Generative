"""
Workspace CRUD service: create, read, update, delete workspaces
and manage members with role-based access.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


VALID_ROLES = {"owner", "admin", "analyst", "viewer"}


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace does not exist."""


class WorkspaceAccessError(Exception):
    """Raised when a user is not allowed to perform an action."""


class WorkspaceStoreError(Exception):
    """Raised when Supabase operation fails."""


class MemberNotFoundError(Exception):
    """Raised when a member is not found in a workspace."""


def _headers() -> dict:
    """Supabase REST headers with service role key."""
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(path: str) -> str:
    """Build Supabase REST URL."""
    return f"{settings.SUPABASE_URL}/rest/v1/{path}"


def _slugify(name: str) -> str:
    """Convert a workspace name into a URL-safe slug."""
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    suffix = uuid.uuid4().hex[:6]
    return f"{base}-{suffix}" if base else f"ws-{suffix}"


def _validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise WorkspaceAccessError(
            f"Invalid role '{role}'. Allowed: {sorted(VALID_ROLES)}"
        )


async def create_workspace(
    owner_id: str,
    name: str,
    plan: str = "free",
) -> dict:
    """
    Create a new workspace and register the creator as owner.
    Returns the workspace record with a `members` sub-object omitted.
    """
    if not name or not name.strip():
        raise WorkspaceStoreError("Workspace name is required")

    slug = _slugify(name)
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "name": name.strip(),
        "slug": slug,
        "owner_id": owner_id,
        "plan": plan,
        "setup_progress": {},
        "setup_completed": False,
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspaces"),
            headers=_headers(),
            json=payload,
        )

    if response.status_code not in (200, 201):
        logger.error(f"[ERROR] Create workspace failed: {response.status_code} {response.text}")
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    workspace = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Workspace created: {workspace['id']} ({slug})")

    await add_member(workspace["id"], owner_id, "owner")
    return workspace


async def get_workspace(workspace_id: str) -> dict:
    """Fetch a single workspace by id."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspaces"),
            headers=_headers(),
            params={
                "id": f"eq.{workspace_id}",
                "select": "*",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise WorkspaceNotFoundError(f"Workspace {workspace_id} not found")

    return rows[0]


async def list_user_workspaces(user_id: str) -> list[dict]:
    """
    List all workspaces where the user is a member.
    Uses a nested select to fetch memberships in one query.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_members"),
            headers=_headers(),
            params={
                "user_id": f"eq.{user_id}",
                "select": "role,workspaces(*)",
            },
        )

    if response.status_code != 200:
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    results = []
    for row in response.json():
        ws = row.get("workspaces")
        if ws:
            ws["role"] = row["role"]
            results.append(ws)
    return results


async def update_workspace(
    workspace_id: str,
    updates: dict,
) -> dict:
    """
    Update workspace metadata (name, plan, setup_progress, setup_completed).
    Slug is immutable.
    """
    allowed_fields = {"name", "plan", "setup_progress", "setup_completed"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered:
        raise WorkspaceStoreError("No valid fields to update")

    filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspaces"),
            headers=_headers(),
            params={"id": f"eq.{workspace_id}"},
            json=filtered,
        )

    if response.status_code != 200:
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise WorkspaceNotFoundError(f"Workspace {workspace_id} not found")

    logger.info(f"[SUCCESS] Workspace updated: {workspace_id}")
    return rows[0]


async def delete_workspace(workspace_id: str, requester_id: str) -> bool:
    """
    Delete a workspace. Only the owner can delete.
    Cascade removes members, secrets, datasets, etc.
    """
    workspace = await get_workspace(workspace_id)
    if workspace["owner_id"] != requester_id:
        raise WorkspaceAccessError("Only the owner can delete this workspace")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspaces"),
            headers=_headers(),
            params={"id": f"eq.{workspace_id}"},
        )

    if response.status_code not in (200, 204):
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Workspace deleted: {workspace_id}")
    return True


# =====================================================
# Members
# =====================================================

async def add_member(
    workspace_id: str,
    user_id: str,
    role: str,
    invited_by: Optional[str] = None,
) -> dict:
    """Add a member to a workspace. If already exists, role is updated."""
    _validate_role(role)

    payload = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "role": role,
        "invited_by": invited_by,
        "joined_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_members"),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "workspace_id,user_id"},
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Member {user_id} added to {workspace_id} as {role}")
    return response.json()[0] if isinstance(response.json(), list) else response.json()


async def update_role(
    workspace_id: str,
    user_id: str,
    new_role: str,
) -> dict:
    """Update a member's role within a workspace."""
    _validate_role(new_role)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspace_members"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "user_id": f"eq.{user_id}",
            },
            json={"role": new_role},
        )

    if response.status_code != 200:
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise MemberNotFoundError(f"User {user_id} not found in workspace {workspace_id}")

    logger.info(f"[SUCCESS] Role updated: {user_id} -> {new_role} in {workspace_id}")
    return rows[0]


async def remove_member(workspace_id: str, user_id: str) -> bool:
    """Remove a member from a workspace."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_members"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "user_id": f"eq.{user_id}",
            },
        )

    if response.status_code not in (200, 204):
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Member removed: {user_id} from {workspace_id}")
    return True


async def list_members(workspace_id: str) -> list[dict]:
    """List all members of a workspace."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_members"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "*",
            },
        )

    if response.status_code != 200:
        raise WorkspaceStoreError(f"Supabase error {response.status_code}: {response.text}")

    return response.json()