"""
Dashboard API routes.
Powers the custom React frontend with on-demand aggregated data.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.dashboard_query_builder import fetch_class_explorer_data
from app.core.logging import log_process, log_error


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class ClassFilter(BaseModel):
    field: str
    values: list[str] = Field(default_factory=list)


class ClassExplorerRequest(BaseModel):
    classes: list[ClassFilter] = Field(default_factory=list)


@router.post("/class-explorer")
async def class_explorer(payload: ClassExplorerRequest) -> dict:
    """
    Return all chart data for the interactive page.

    Body:
        {
          "classes": [
            {"field": "card_brand", "values": ["Visa", "Mastercard"]},
            {"field": "gender", "values": ["Male"]}
          ]
        }
    """
    log_process(
        f"class-explorer: {len(payload.classes)} class filters, "
        f"{sum(len(c.values) for c in payload.classes)} total values"
    )

    try:
        classes_dicts = [
            {"field": c.field, "values": c.values}
            for c in payload.classes
        ]
        data = await fetch_class_explorer_data(classes_dicts)
        return {"success": True, "data": data, "error": None}
    except Exception as exc:
        log_error(f"class-explorer failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))