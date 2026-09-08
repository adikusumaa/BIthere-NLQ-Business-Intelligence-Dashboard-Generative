"""
Authentication endpoints for BIthere.
Handles user registration and profile retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.security import get_current_user, get_supabase_client, require_role
from app.core.logging import logger


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    """
    Request body for user registration.
    """

    email: EmailStr
    role: str = "analyst"


class UserProfile(BaseModel):
    """
    Response model for user profile.
    """

    id: str
    email: str
    role: str


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterRequest,
    admin_user: dict = Depends(require_role("admin")),
) -> dict:
    """
    Admin-only endpoint to invite new user.
    Creates user in Supabase Auth and stores profile.
    """

    supabase = get_supabase_client()

    try:
        auth_response = supabase.auth.admin.create_user({
            "email": body.email,
            "password": "BIthere123!",
            "email_confirm": True,
        })

        user_id = auth_response.user.id

        supabase.table("profiles").insert({
            "id": user_id,
            "email": body.email,
            "role": body.role,
        }).execute()

        logger.success(f"User {body.email} registered with role {body.role}")

        return {
            "id": user_id,
            "email": body.email,
            "role": body.role,
        }

    except Exception as error:
        logger.error(f"Registration failed: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(error)}",
        )


@router.get("/me", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)) -> dict:
    """
    Returns current user profile based on JWT token.
    """

    logger.info(f"Profile accessed by user {user.get('email')}")

    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
    }