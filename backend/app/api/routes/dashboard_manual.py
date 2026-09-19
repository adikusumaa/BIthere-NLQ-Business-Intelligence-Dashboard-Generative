"""
Dashboard manual edit routes (F-13): patch from drag/resize UI.
Wrapper around apply that additionally pushes to the undo stack
and syncs to Metabase.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.logging import logger
from app.core.security import get_current_user
from app.dashboard import state_store
from app.dashboard import undo_redo
from app.dashboard.conflict_detector import ConflictError, check_conflict
from app.dashboard.lock import LockError, lock
from app.dashboard.patch_applier import PatchApplyError, apply
from app.dashboard.patch_model import parse_patch
from app.dashboard.patch_validator import validate
from app.dashboard.state_store import DashboardNotFoundError, StateStoreError
from app.dashboard.sync_helper import sync_to_metabase
from app.workspace.context import WorkspaceContext, get_workspace_context
from app.dashboard.state_model import find_card


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard Manual Edit (F-13)"],
)


class ManualEditRequest(BaseModel):
    patch: dict
    base_version: int
    session_id: Optional[str] = None


@router.post("/{dashboard_id}/manual-edit")
async def manual_edit_endpoint(
    workspace_id: str,
    dashboard_id: str,
    body: ManualEditRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Apply a patch that originated from a UI drag/resize/property edit.
    Same pipeline as patch/apply, plus undo stack push and Metabase sync.
    """
    try:
        async with lock(dashboard_id):
            try:
                await check_conflict(dashboard_id, body.base_version)
            except ConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc))

            state = await state_store.load_latest(dashboard_id)

            try:
                patch = parse_patch(body.patch)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid patch: {exc}")

            result = validate(patch, state)
            if not result.valid:
                raise HTTPException(status_code=400, detail=f"Validation failed: {result.reason}")

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

            if body.session_id:
                await undo_redo.push_undo(body.session_id, patch)

            logger.info(
                f"[SUCCESS] Manual edit: dashboard={dashboard_id} "
                f"v{state.version} -> v{new_state.version}"
            )

            return {
                "version": new_state.version,
                "state": new_state.model_dump(mode="json"),
                "actions_count": len(actions),
                "metabase_results": metabase_results,
            }
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))