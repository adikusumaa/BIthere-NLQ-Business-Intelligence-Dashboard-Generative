"""
Dashboard version routes (F-13): rollback + diff.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.dashboard import state_store
from app.dashboard import version_control
from app.dashboard.conflict_detector import ConflictError, check_conflict
from app.dashboard.lock import LockError, lock
from app.dashboard.state_store import DashboardNotFoundError, StateStoreError
from app.dashboard.version_control import VersionControlError
from app.workspace.context import WorkspaceContext, get_workspace_context


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard Version (F-13)"],
)


class RollbackRequest(BaseModel):
    target_version: int
    base_version: int


@router.post("/{dashboard_id}/rollback")
async def rollback_endpoint(
    workspace_id: str,
    dashboard_id: str,
    body: RollbackRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        async with lock(dashboard_id):
            try:
                await check_conflict(dashboard_id, body.base_version)
            except ConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc))

            new_state = await version_control.rollback(
                dashboard_id=dashboard_id,
                target_version=body.target_version,
                user_id=user["id"],
            )
            return new_state.model_dump(mode="json")
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except VersionControlError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dashboard_id}/diff")
async def diff_endpoint(
    workspace_id: str,
    dashboard_id: str,
    v1: int,
    v2: int,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        a = await state_store.load_version(dashboard_id, v1)
        b = await state_store.load_version(dashboard_id, v2)
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="One of the versions not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return version_control.diff_states(a, b)