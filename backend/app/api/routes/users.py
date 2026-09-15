"""
Admin-only user management routes.

Wraps Supabase Auth admin API and the profiles table.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.security import get_supabase_client, require_role
from app.core.logging import log_process, log_error


router = APIRouter(prefix="/api/users", tags=["users"])


class UserSummary(BaseModel):
    id: str
    email: str
    role: str
    created_at: str | None


class InviteUserRequest(BaseModel):
    email: str
    role: str = Field(default="analyst", pattern="^(admin|analyst)$")
    password: str = Field(..., min_length=6, max_length=72)


class UpdateUserRequest(BaseModel):
    role: str = Field(..., pattern="^(admin|analyst)$")


def _to_summary(row: dict[str, Any]) -> UserSummary:
    return UserSummary(
        id=row.get("id"),
        email=row.get("email", ""),
        role=row.get("role", "analyst"),
        created_at=row.get("created_at"),
    )


@router.get("", response_model=list[UserSummary])
async def list_users(
    admin: dict = Depends(require_role("admin")),
) -> list[UserSummary]:
    """List all users from the profiles table."""
    log_process(f"users: list by admin={admin.get('email')}")

    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("profiles")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        log_error(f"users: list failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users",
        )

    return [_to_summary(row) for row in response.data or []]


@router.post("", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
async def invite_user(
    payload: InviteUserRequest,
    admin: dict = Depends(require_role("admin")),
) -> UserSummary:
    """Create a new user via Supabase Auth and add a profile row."""
    log_process(f"users: invite {payload.email} role={payload.role}")

    supabase = get_supabase_client()

    try:
        auth_response = supabase.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
        })
    except Exception as exc:
        log_error(f"users: supabase auth create failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create auth user: {exc}",
        )

    new_user = getattr(auth_response, "user", None)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase returned no user",
        )

    try:
        supabase.table("profiles").insert({
            "id": new_user.id,
            "email": payload.email,
            "role": payload.role,
        }).execute()

        profile = (
            supabase.table("profiles")
            .select("*")
            .eq("id", new_user.id)
            .execute()
        )
    except Exception as exc:
        log_error(f"users: profile insert failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auth user created but profile insert failed: {exc}",
        )

    if not profile.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile not found after insert",
        )

    return _to_summary(profile.data[0])


@router.put("/{user_id}", response_model=UserSummary)
async def update_user_role(
    user_id: str,
    payload: UpdateUserRequest,
    admin: dict = Depends(require_role("admin")),
) -> UserSummary:
    """Update the role of a user in the profiles table."""
    log_process(f"users: update {user_id} role={payload.role}")

    supabase = get_supabase_client()
    try:
        response = (
            supabase.table("profiles")
            .update({"role": payload.role})
            .eq("id", user_id)
            .execute()
        )
    except Exception as exc:
        log_error(f"users: update failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _to_summary(response.data[0])


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_role("admin")),
) -> dict[str, Any]:
    """Delete a user from both Auth and profiles."""
    log_process(f"users: delete {user_id}")

    if user_id == admin.get("id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    supabase = get_supabase_client()

    try:
        supabase.auth.admin.delete_user(user_id)
    except Exception as exc:
        log_error(f"users: auth delete failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete auth user: {exc}",
        )

    try:
        supabase.table("profiles").delete().eq("id", user_id).execute()
    except Exception as exc:
        log_error(f"users: profile delete failed: {exc}")

    return {"success": True, "user_id": user_id, "error": None}