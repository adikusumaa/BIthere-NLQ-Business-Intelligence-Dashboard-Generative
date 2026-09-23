"""
Generic progress polling endpoint.
"""

from fastapi import APIRouter, Depends

from app.core.progress import get_job
from app.core.security import get_current_user


router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/{key}")
async def get_progress(key: str, user: dict = Depends(get_current_user)) -> dict:
    job = get_job(key)
    if not job:
        return {"status": "idle"}
    return job