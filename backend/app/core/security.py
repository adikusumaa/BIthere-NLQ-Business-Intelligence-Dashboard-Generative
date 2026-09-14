"""
Authentication and authorization utilities for BIthere.
Validates Supabase tokens via the Supabase Auth API.
"""

from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.core.config import settings
from app.core.logging import logger


bearer_scheme = HTTPBearer(auto_error=False)


def get_supabase_client() -> Client:
    """Return a Supabase client using the service role key."""

    return create_client(
        settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
    )


async def _verify_token_with_supabase(token: str) -> dict:
    """Verify a Supabase access token by calling the Auth API."""

    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
    except Exception as error:
        logger.error(f"Supabase auth call failed: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication service unavailable",
        )

    if response.status_code != 200:
        logger.error(
            f"Supabase rejected token ({response.status_code}): "
            f"{response.text[:200]}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    return response.json()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """Extract user info from the Authorization header."""

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials
    user_payload = await _verify_token_with_supabase(token)

    user_id = user_payload.get("id")
    email = user_payload.get("email")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    role = "analyst"
    try:
        supabase = get_supabase_client()
        profile = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )
        if profile.data:
            role = profile.data[0].get("role", "analyst")
    except Exception as error:
        logger.warning(f"Profile lookup failed, using default role: {error}")

    return {
        "id": user_id,
        "email": email,
        "role": role,
    }


def require_role(required_role: str):
    """Dependency factory that enforces a specific role."""

    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role",
            )
        return user

    return role_checker