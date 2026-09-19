"""
Dashboard state store: persist and retrieve versioned dashboard states
backed by Supabase tables `dashboard_versions` and `dashboard_patches`.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.dashboard.state_model import DashboardState


class StateStoreError(Exception):
    """Raised when a Supabase operation fails."""


class DashboardNotFoundError(Exception):
    """Raised when no versions exist for a dashboard."""


def _headers() -> dict:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(path: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{path}"


def _patch_hash(patch: Any) -> str:
    """Stable hash of a patch for idempotency checks."""
    if patch is None:
        return ""
    if hasattr(patch, "model_dump"):
        payload = patch.model_dump(mode="json")
    else:
        payload = patch
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def save_version(
    dashboard_id: str,
    state: DashboardState,
    patch: Optional[Any] = None,
    user_id: Optional[str] = None,
    patch_status: str = "applied",
    from_version: Optional[int] = None,
) -> dict:
    """
    Save a new version of the dashboard state.
    Optionally records the patch that produced it.

    Returns the inserted version row.
    """
    now = datetime.now(timezone.utc).isoformat()

    state_payload = state.model_dump(mode="json")
    state_payload["version"] = state.version
    state_payload["parent_version"] = state.parent_version
    state_payload["created_at"] = now

    version_row = {
        "dashboard_id": dashboard_id,
        "workspace_id": state.workspace_id,
        "version": state.version,
        "parent_version": state.parent_version,
        "state_json": state_payload,
        "patch_applied": patch.model_dump(mode="json") if patch and hasattr(patch, "model_dump") else patch,
        "created_by": user_id,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _rest_url("dashboard_versions"),
            headers=_headers(),
            json=version_row,
        )

    if response.status_code not in (200, 201):
        logger.error(f"[ERROR] save_version failed: {response.status_code} {response.text}")
        raise StateStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )

    inserted = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(
        f"[SUCCESS] Dashboard version saved: dashboard={dashboard_id} v{state.version}"
    )

    if patch is not None:
        await _record_patch(
            dashboard_id=dashboard_id,
            workspace_id=state.workspace_id,
            from_version=from_version if from_version is not None else (state.parent_version or 0),
            to_version=state.version,
            patch=patch,
            status=patch_status,
            user_id=user_id,
        )

    return inserted


async def _record_patch(
    dashboard_id: str,
    workspace_id: str,
    from_version: int,
    to_version: int,
    patch: Any,
    status: str,
    user_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    payload = {
        "dashboard_id": dashboard_id,
        "workspace_id": workspace_id,
        "from_version": from_version,
        "to_version": to_version,
        "patch_json": patch.model_dump(mode="json") if hasattr(patch, "model_dump") else patch,
        "patch_hash": _patch_hash(patch),
        "status": status,
        "error_message": error_message,
        "created_by": user_id,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _rest_url("dashboard_patches"),
            headers=_headers(),
            json=payload,
        )

    if response.status_code not in (200, 201):
        logger.error(f"[ERROR] record_patch failed: {response.status_code} {response.text}")
        raise StateStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )


async def load_version(dashboard_id: str, version: int) -> DashboardState:
    """Load a specific version of a dashboard."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            _rest_url("dashboard_versions"),
            headers=_headers(),
            params={
                "dashboard_id": f"eq.{dashboard_id}",
                "version": f"eq.{version}",
                "select": "state_json",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise StateStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise DashboardNotFoundError(
            f"No version {version} for dashboard {dashboard_id}"
        )

    return DashboardState.model_validate(rows[0]["state_json"])


async def load_latest(dashboard_id: str) -> DashboardState:
    """Load the latest version of a dashboard."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            _rest_url("dashboard_versions"),
            headers=_headers(),
            params={
                "dashboard_id": f"eq.{dashboard_id}",
                "select": "state_json",
                "order": "version.desc",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise StateStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise DashboardNotFoundError(
            f"No versions found for dashboard {dashboard_id}"
        )

    return DashboardState.model_validate(rows[0]["state_json"])


async def list_versions(dashboard_id: str) -> List[Dict[str, Any]]:
    """
    List all versions (summary only — no full state payload).
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            _rest_url("dashboard_versions"),
            headers=_headers(),
            params={
                "dashboard_id": f"eq.{dashboard_id}",
                "select": "id,version,parent_version,created_by,created_at",
                "order": "version.desc",
            },
        )

    if response.status_code != 200:
        raise StateStoreError(f"Supabase error {response.status_code}: {response.text}")

    return response.json()


async def get_patches(
    dashboard_id: str,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return the patch log for a dashboard, newest first."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            _rest_url("dashboard_patches"),
            headers=_headers(),
            params={
                "dashboard_id": f"eq.{dashboard_id}",
                "select": "*",
                "order": "created_at.desc",
                "limit": str(limit),
            },
        )

    if response.status_code != 200:
        raise StateStoreError(f"Supabase error {response.status_code}: {response.text}")

    return response.json()


async def delete_dashboard(dashboard_id: str) -> bool:
    """Delete all versions and patches for a dashboard."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        await client.delete(
            _rest_url("dashboard_versions"),
            headers=_headers(),
            params={"dashboard_id": f"eq.{dashboard_id}"},
        )
        await client.delete(
            _rest_url("dashboard_patches"),
            headers=_headers(),
            params={"dashboard_id": f"eq.{dashboard_id}"},
        )

    logger.info(f"[SUCCESS] Dashboard deleted: {dashboard_id}")
    return True