"""
Authentication and authorization utilities for BIthere.
Handles JWT verification against Supabase Auth.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from supabase import Client, create_client

from app.core.config import settings
from app.core.logging import logger


bearer_scheme = HTTPBearer(auto_error=False)


def get_supabase_client() -> Client:
    """
    Returns a Supabase client instance using service role key.
    """

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def verify_jwt_token(token: str) -> dict:
    """
    Verifies JWT token from Supabase and returns payload.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as error:
        logger.error(f"JWT verification failed: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Extracts user information from JWT token.
    Returns user payload with id and email.
    """

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials
    payload = verify_jwt_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    supabase = get_supabase_client()
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found",
        )

    return response.data[0]


def require_role(required_role: str):
    """
    Dependency factory to check user role.
    Usage: Depends(require_role("admin"))
    """

    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role",
            )
        return user

    return role_checker