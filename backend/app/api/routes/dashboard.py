"""
Dashboard API routes.

Provides NLQ-driven dashboard creation, listing, and deletion.
Persists dashboard metadata to the Supabase table dashboard_configs.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.dashboard_builder import build_dashboard
from app.api.deps import get_current_user
from app.core.security import get_supabase_client
from app.core.logging import log_process, log_error


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class CreateDashboardRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)


class DashboardSummary(BaseModel):
    id: int
    user_id: str
    metabase_dashboard_id: int | None
    embed_url: str | None
    title: str | None
    created_at: str | None


class CreateDashboardResponse(BaseModel):
    success: bool
    dashboard_id: int | None
    metabase_dashboard_id: int | None
    embed_url: str | None
    title: str | None
    error: str | None


def _row_to_summary(row: dict[str, Any]) -> DashboardSummary:
    """Map a dashboard_configs row to a summary model."""
    config = row.get("config_json") or {}
    return DashboardSummary(
        id=row.get("id"),
        user_id=row.get("user_id"),
        metabase_dashboard_id=row.get("metabase_dashboard_id"),
        embed_url=row.get("embed_url"),
        title=config.get("title"),
        created_at=row.get("created_at"),
    )


@router.post("", response_model=CreateDashboardResponse)
async def create_dashboard(
    payload: CreateDashboardRequest,
    user: dict = Depends(get_current_user),
) -> CreateDashboardResponse:
    """Build a dashboard from a natural-language prompt and persist it."""
    log_process(f"dashboard: create for user={user.get('email')}")

    result = await build_dashboard(payload.prompt)

    if not result.get("success"):
        log_error(f"dashboard: builder failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error") or "Failed to build dashboard",
        )

    config = result.get("config") or {}
    title = config.get("title")

    try:
        supabase = get_supabase_client()
        insert_payload = {
            "user_id": user["id"],
            "metabase_dashboard_id": result.get("dashboard_id"),
            "config_json": config,
            "embed_url": result.get("embed_url"),
        }
        insert_response = (
            supabase.table("dashboard_configs").insert(insert_payload).execute()
        )
    except Exception as exc:
        log_error(f"dashboard: persistence failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard created in Metabase but not saved to database",
        )

    saved_row = insert_response.data[0] if insert_response.data else {}
    log_process(f"dashboard: saved id={saved_row.get('id')}")

    return CreateDashboardResponse(
        success=True,
        dashboard_id=saved_row.get("id"),
        metabase_dashboard_id=result.get("dashboard_id"),
        embed_url=result.get("embed_url"),
        title=title,
        error=None,
    )


@router.get("", response_model=list[DashboardSummary])
async def list_dashboards(
    user: dict = Depends(get_current_user),
) -> list[DashboardSummary]:
    """List all dashboards owned by the current user."""
    log_process(f"dashboard: list for user={user.get('email')}")

    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("dashboard_configs")
            .select("*")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        log_error(f"dashboard: list failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboards",
        )

    return [_row_to_summary(row) for row in response.data or []]


@router.get("/{dashboard_id}", response_model=DashboardSummary)
async def get_dashboard(
    dashboard_id: int,
    user: dict = Depends(get_current_user),
) -> DashboardSummary:
    """Fetch a single dashboard by ID."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("dashboard_configs")
            .select("*")
            .eq("id", dashboard_id)
            .eq("user_id", user["id"])
            .execute()
        )
    except Exception as exc:
        log_error(f"dashboard: fetch failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard",
        )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    return _row_to_summary(response.data[0])


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a dashboard owned by the current user."""
    log_process(f"dashboard: delete id={dashboard_id} user={user.get('email')}")

    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("dashboard_configs")
            .delete()
            .eq("id", dashboard_id)
            .eq("user_id", user["id"])
            .execute()
        )
    except Exception as exc:
        log_error(f"dashboard: delete failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete dashboard",
        )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )

    return {"success": True, "dashboard_id": dashboard_id, "error": None}