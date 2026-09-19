"""
Dashboard undo/redo routes (F-13).
Both endpoints sync their effect to Metabase.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.logging import logger
from app.core.security import get_current_user
from app.dashboard import undo_redo
from app.dashboard import state_store
from app.dashboard.diff_actions import diff_to_actions
from app.dashboard.lock import LockError, lock
from app.dashboard.patch_model import parse_patch
from app.dashboard.patch_applier import PatchApplyError, apply
from app.dashboard.state_model import find_card
from app.dashboard.state_store import DashboardNotFoundError, StateStoreError
from app.dashboard.sync_helper import sync_to_metabase
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
    Undo: pop last patch from session undo stack, restore parent version,
    and sync the diff to Metabase.
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

            # Diff current vs parent -> sync actions
            actions = diff_to_actions(current, parent)

            from copy import deepcopy
            new_state = deepcopy(parent)
            new_state.parent_version = current.version
            new_state.version = current.version + 1

            metabase_results, _ = await sync_to_metabase(
                new_state.metabase_dashboard_id,
                actions,
            )

            await state_store.save_version(
                dashboard_id=dashboard_id,
                state=new_state,
                patch=parse_patch(patch_dict),
                user_id=user["id"],
                from_version=current.version,
                patch_status="rolled_back",
            )

            logger.info(
                f"[SUCCESS] Undo: dashboard={dashboard_id} "
                f"v{current.version} -> v{new_state.version}"
            )

            return {
                "version": new_state.version,
                "state": new_state.model_dump(mode="json"),
                "metabase_results": metabase_results,
            }
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
    """
    Redo: pop from redo stack, reapply the patch, and sync to Metabase.
    """
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

            try:
                new_state, actions = apply(state, patch)
            except PatchApplyError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

            metabase_results, refs = await sync_to_metabase(
                new_state.metabase_dashboard_id,
                actions,
            )

            for cid, ref in refs.items():
                card = find_card(new_state, cid)
                if card:
                    if ref.get("mb_card_id"):
                        card.metabase.card_id = ref["mb_card_id"]
                    if ref.get("mb_dashcard_id"):
                        card.metabase.dashcard_id = ref["mb_dashcard_id"]

            await state_store.save_version(
                dashboard_id=dashboard_id,
                state=new_state,
                patch=patch,
                user_id=user["id"],
                from_version=state.version,
            )

            logger.info(
                f"[SUCCESS] Redo: dashboard={dashboard_id} "
                f"v{state.version} -> v{new_state.version}"
            )

            return {
                "version": new_state.version,
                "state": new_state.model_dump(mode="json"),
                "metabase_results": metabase_results,
            }
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except PatchApplyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))