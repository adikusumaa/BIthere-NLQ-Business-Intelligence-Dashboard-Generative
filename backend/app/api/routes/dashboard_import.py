"""
Dashboard import route (F-13): convert a Metabase dashboard to F-13 state.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.dashboard.importer import ImportError, import_from_metabase
from app.workspace.context import WorkspaceContext, get_workspace_context


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard Import (F-13)"],
)


class ImportRequest(BaseModel):
    metabase_dashboard_id: int
    name: Optional[str] = None


@router.post("/import")
async def import_dashboard(
    workspace_id: str,
    body: ImportRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        state = await import_from_metabase(
            workspace_id=workspace_id,
            metabase_dashboard_id=body.metabase_dashboard_id,
            user_id=user["id"],
            name_override=body.name,
        )
        return {
            "dashboard_id": state.dashboard_id,
            "version": state.version,
            "cards_count": sum(len(p.cards) for p in state.pages),
            "state": state.model_dump(mode="json"),
        }
    except ImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))