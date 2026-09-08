"""
FastAPI dependencies for authentication and role checking.
"""

from app.core.security import get_current_user, require_role


__all__ = ["get_current_user", "require_role"]