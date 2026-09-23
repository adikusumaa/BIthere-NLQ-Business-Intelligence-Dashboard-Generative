"""
Workspace management endpoints.
Includes member management and email-based invites.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_current_user
from app.workspace import invites as invite_store
from app.workspace import service as ws_service
from app.workspace.service import (
    WorkspaceAccessError,
    WorkspaceNotFoundError,
    WorkspaceStoreError,
)


router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    plan: str = "free"


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    plan: str | None = None
    setup_progress: dict | None = None
    setup_completed: bool | None = None


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "analyst"


class UpdateRoleRequest(BaseModel):
    role: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "analyst"


@router.get("")
async def list_my_workspaces(user: dict = Depends(get_current_user)) -> list[dict]:
    """List all workspaces the current user is a member of."""
    try:
        return await ws_service.list_user_workspaces(user["id"])
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: CreateWorkspaceRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Create a new workspace; creator becomes owner.
    If ALLOW_WORKSPACE_CREATION is admin_only, only admin role can call this.
    """
    if settings.ALLOW_WORKSPACE_CREATION == "admin_only":
        if user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace creation is restricted to administrators",
            )
    try:
        workspace = await ws_service.create_workspace(
            owner_id=user["id"],
            name=body.name,
            plan=body.plan,
        )
        logger.info(f"[SUCCESS] Workspace created via API: {workspace['id']}")
        return workspace
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        workspace = await ws_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    members = await ws_service.list_members(workspace_id)
    if not any(m["user_id"] == user["id"] for m in members):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return workspace


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        workspace = await ws_service.get_workspace(workspace_id)
        if workspace["owner_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only owner can update workspace")

        updates = body.model_dump(exclude_none=True)
        return await ws_service.update_workspace(workspace_id, updates)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await ws_service.delete_workspace(workspace_id, user["id"])
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await ws_service.list_members(workspace_id)
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: str,
    body: AddMemberRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        return await ws_service.add_member(
            workspace_id, body.user_id, body.role, invited_by=user["id"]
        )
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/{workspace_id}/members/{user_id}")
async def update_member_role(
    workspace_id: str,
    user_id: str,
    body: UpdateRoleRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        return await ws_service.update_role(workspace_id, user_id, body.role)
    except WorkspaceAccessError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: str,
    user_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await ws_service.remove_member(workspace_id, user_id)
    except WorkspaceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{workspace_id}/invites", status_code=status.HTTP_201_CREATED)
async def create_invite(
    workspace_id: str,
    body: InviteRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Owner or admin invites an email to join the workspace."""
    members = await ws_service.list_members(workspace_id)
    actor = next((m for m in members if m["user_id"] == user["id"]), None)
    if not actor or actor["role"] not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Only owner or admin can invite")
    try:
        return await invite_store.create_invite(
            workspace_id=workspace_id,
            email=body.email,
            role=body.role,
            invited_by=user["id"],
        )
    except invite_store.InviteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{workspace_id}/invites")
async def list_invites(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await invite_store.list_invites(workspace_id)
    except invite_store.InviteError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{workspace_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    workspace_id: str,
    invite_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await invite_store.revoke_invite(invite_id)
    except invite_store.InviteError as exc:
        raise HTTPException(status_code=500, detail=str(exc))