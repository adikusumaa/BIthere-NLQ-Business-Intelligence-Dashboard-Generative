"""
Authentication endpoints for BIthere.
Handles self-register, admin invite, and profile retrieval.
New users are automatically joined to any workspace that has a pending
invite matching their email.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_current_user, get_supabase_client, require_role
from app.workspace import invites as invite_store


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class AdminInviteUserRequest(BaseModel):
    email: EmailStr
    role: str = "analyst"


class UserProfile(BaseModel):
    id: str
    email: str
    role: str


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(body: RegisterRequest) -> dict:
    """
    Self-register a user.
    If ALLOW_SELF_REGISTER is false, the email must have a pending invite
    for at least one workspace.
    """
    email = body.email.lower()

    if not settings.ALLOW_SELF_REGISTER:
        pending = await invite_store.list_pending_for_email(email)
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is invite-only. Contact your administrator.",
            )

    supabase = get_supabase_client()

    try:
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": body.password,
            "email_confirm": True,
        })
    except Exception as exc:
        message = str(exc).lower()
        if "already" in message or "duplicate" in message or "registered" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        logger.error(f"[ERROR] Register failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        )

    user_id = auth_response.user.id

    try:
        supabase.table("profiles").insert({
            "id": user_id,
            "email": email,
            "role": "analyst",
        }).execute()
    except Exception as exc:
        logger.error(f"[ERROR] Profile creation failed: {exc}")

    joined = await invite_store.accept_pending_invites_for_user(user_id, email)
    logger.info(
        f"[SUCCESS] User registered: {email} joined={len(joined)} workspace(s)"
    )

    return {
        "id": user_id,
        "email": email,
        "role": "analyst",
    }


@router.post("/invite", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def admin_invite_user(
    body: AdminInviteUserRequest,
    admin_user: dict = Depends(require_role("admin")),
) -> dict:
    """
    Admin-only endpoint: create a user account from an admin panel.
    """
    email = body.email.lower()
    supabase = get_supabase_client()

    try:
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": "TemporaryPass123!",
            "email_confirm": True,
        })
        user_id = auth_response.user.id

        supabase.table("profiles").insert({
            "id": user_id,
            "email": email,
            "role": body.role,
        }).execute()

        logger.info(f"[SUCCESS] Admin invited user: {email} role={body.role}")
        return {
            "id": user_id,
            "email": email,
            "role": body.role,
        }
    except Exception as exc:
        message = str(exc).lower()
        if "already" in message or "duplicate" in message or "registered" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
        logger.error(f"[ERROR] Admin invite failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/me", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)) -> dict:
    """
    Returns the current user profile based on JWT token.
    Also attempts to auto-accept any pending workspace invites for the email.
    """
    logger.info(f"[PROCESS] Profile accessed by {user.get('email')}")

    try:
        joined = await invite_store.accept_pending_invites_for_user(
            user_id=user["id"],
            email=user.get("email", ""),
        )
        if joined:
            logger.info(
                f"[PROCESS] Auto-joined {len(joined)} workspace(s) "
                f"for {user.get('email')}"
            )
    except Exception as exc:
        logger.error(f"[ERROR] Auto-join invites failed: {exc}")

    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
    }