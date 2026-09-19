"""
Dashboard state routes (F-13): read-only inspection.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.dashboard import state_store
from app.dashboard.state_store import (
    DashboardNotFoundError,
    StateStoreError,
)
from app.workspace.context import WorkspaceContext, get_workspace_context


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard State (F-13)"],
)


@router.get("/{dashboard_id}/state")
async def get_state(
    workspace_id: str,
    dashboard_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        state = await state_store.load_latest(dashboard_id)
        return state.model_dump(mode="json")
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dashboard_id}/versions")
async def list_versions(
    workspace_id: str,
    dashboard_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await state_store.list_versions(dashboard_id)
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dashboard_id}/versions/{version}")
async def get_version(
    workspace_id: str,
    dashboard_id: str,
    version: int,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        state = await state_store.load_version(dashboard_id, version)
        return state.model_dump(mode="json")
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Version not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dashboard_id}/patches")
async def list_patches(
    workspace_id: str,
    dashboard_id: str,
    limit: int = 100,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await state_store.get_patches(dashboard_id, limit=limit)
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))