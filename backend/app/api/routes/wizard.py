"""
Setup wizard state management.
Persists progress in workspaces.setup_progress so users can resume.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.workspace import service as ws_service
from app.workspace.service import WorkspaceNotFoundError, WorkspaceStoreError


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/wizard",
    tags=["Wizard"],
)


VALID_STEPS = {
    1: "account",
    2: "api_keys",
    3: "data_source",
    4: "dataset_upload",
    5: "schema_builder",
    6: "knowledge_base",
}


class SaveStepRequest(BaseModel):
    data: Optional[dict[str, Any]] = None


@router.get("/state")
async def get_wizard_state(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Return current wizard progress."""
    try:
        workspace = await ws_service.get_workspace(workspace_id)
        return {
            "workspace_id": workspace["id"],
            "setup_progress": workspace.get("setup_progress") or {},
            "setup_completed": workspace.get("setup_completed", False),
            "steps": VALID_STEPS,
        }
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/step/{step}")
async def save_step(
    workspace_id: str,
    step: int,
    body: SaveStepRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Persist progress for a single wizard step."""
    if step not in VALID_STEPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step {step}. Valid: {sorted(VALID_STEPS.keys())}",
        )

    try:
        workspace = await ws_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    progress = workspace.get("setup_progress") or {}
    progress[str(step)] = {
        "name": VALID_STEPS[step],
        "data": body.data or {},
        "completed": True,
    }

    try:
        updated = await ws_service.update_workspace(
            workspace_id, {"setup_progress": progress}
        )
        return {"step": step, "setup_progress": updated.get("setup_progress")}
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/complete")
async def complete_wizard(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Mark wizard as complete; workspace is ready for chat."""
    try:
        workspace = await ws_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    progress = workspace.get("setup_progress") or {}
    missing = [s for s in VALID_STEPS if str(s) not in progress]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Steps not completed: {missing}",
        )

    try:
        updated = await ws_service.update_workspace(
            workspace_id, {"setup_completed": True}
        )
        return {"workspace_id": workspace_id, "setup_completed": True}
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
async def reset_wizard(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Reset wizard progress (for demo / re-onboarding)."""
    try:
        await ws_service.update_workspace(
            workspace_id,
            {"setup_progress": {}, "setup_completed": False},
        )
        return {"workspace_id": workspace_id, "reset": True}
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))