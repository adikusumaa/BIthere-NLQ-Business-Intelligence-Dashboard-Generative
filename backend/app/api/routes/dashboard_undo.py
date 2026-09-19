"""
Dashboard undo/redo routes (F-13).
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.dashboard import undo_redo
from app.dashboard.lock import LockError, lock
from app.dashboard.patch_model import parse_patch
from app.dashboard.patch_applier import PatchApplyError, apply
from app.dashboard import state_store
from app.dashboard.state_store import DashboardNotFoundError, StateStoreError
from app.workspace.context import WorkspaceContext, get_workspace_context


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard Undo/Redo (F-13)"],
)


@router.post("/{dashboard_id}/undo")
async def undo_endpoint(
    workspace_id: str,
    dashboard_id: str,
    session_id: str = Query(...),
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Pop the last patch from the session undo stack and apply its inverse
    by loading the parent version of the current state.
    """
    patch_dict = await undo_redo.undo(session_id)
    if not patch_dict:
        raise HTTPException(status_code=400, detail="Nothing to undo")

    try:
        async with lock(dashboard_id):
            current = await state_store.load_latest(dashboard_id)
            if current.parent_version is None:
                raise HTTPException(status_code=400, detail="No parent version to undo to")

            parent = await state_store.load_version(dashboard_id, current.parent_version)

            # Create a new version that is a copy of parent
            from copy import deepcopy
            new_state = deepcopy(parent)
            new_state.parent_version = current.version
            new_state.version = current.version + 1

            await state_store.save_version(
                dashboard_id=dashboard_id,
                state=new_state,
                patch=parse_patch(patch_dict),
                user_id=user["id"],
                from_version=current.version,
                patch_status="rolled_back",
            )
            return new_state.model_dump(mode="json")
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{dashboard_id}/redo")
async def redo_endpoint(
    workspace_id: str,
    dashboard_id: str,
    session_id: str = Query(...),
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    patch_dict = await undo_redo.redo(session_id)
    if not patch_dict:
        raise HTTPException(status_code=400, detail="Nothing to redo")

    try:
        async with lock(dashboard_id):
            state = await state_store.load_latest(dashboard_id)
            try:
                patch = parse_patch(patch_dict)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid patch: {exc}")

            new_state, _ = apply(state, patch)

            await state_store.save_version(
                dashboard_id=dashboard_id,
                state=new_state,
                patch=patch,
                user_id=user["id"],
                from_version=state.version,
            )
            return new_state.model_dump(mode="json")
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except PatchApplyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))