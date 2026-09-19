"""
Dashboard patch routes (F-13): parse NL -> patch, apply patch.
Both endpoints inject the workspace schema hint into the intent parser.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.logging import logger
from app.core.security import get_current_user
from app.dashboard import state_store
from app.dashboard.conflict_detector import ConflictError, check_conflict
from app.dashboard.intent_parser import IntentParseError, parse_instruction
from app.dashboard.lock import LockError, lock
from app.dashboard.patch_applier import PatchApplyError, apply
from app.dashboard.patch_model import parse_patch
from app.dashboard.patch_validator import validate
from app.dashboard.state_model import find_card
from app.dashboard.state_store import DashboardNotFoundError, StateStoreError
from app.dashboard.sync_helper import sync_to_metabase
from app.workspace.context import WorkspaceContext, get_workspace_context


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/dashboards",
    tags=["Dashboard Patch (F-13)"],
)


class ParseRequest(BaseModel):
    instruction: str


class ApplyRequest(BaseModel):
    patch: Optional[dict] = None
    instruction: Optional[str] = None
    base_version: int


async def _load_schema_hint(workspace_id: str) -> str:
    """
    Build a compact schema description from the workspace's default connector.
    Skips internal BIthere tables.
    """
    internal = {
        "profiles", "query_history", "dashboard_configs", "business_glossary",
        "ingestion_logs", "audit_logs", "usage_events",
        "dashboard_versions", "dashboard_patches",
    }
    try:
        from app.workspace.data_sources import get_workspace_connector
        connector = await get_workspace_connector(workspace_id)
        await connector.connect()
        try:
            schema = await connector.get_schema()
        finally:
            await connector.disconnect()

        lines = []
        for table, columns in schema.items():
            if table in internal or table.startswith("workspace_"):
                continue
            cols = ", ".join(c["column"] for c in columns)
            lines.append(f"{table}({cols})")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[WARNING] Could not load schema hint: {exc}")
        return ""


@router.post("/{dashboard_id}/patch/parse")
async def parse_patch_endpoint(
    workspace_id: str,
    dashboard_id: str,
    body: ParseRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """Parse NL instruction into a patch (no apply)."""
    try:
        state = await state_store.load_latest(dashboard_id)
    except DashboardNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    schema_hint = await _load_schema_hint(workspace_id)

    try:
        patch = await parse_instruction(
            body.instruction,
            state,
            api_key=ctx.groq_key,
            redis_prefix=ctx.redis_prefix,
            schema_hint=schema_hint,
        )
    except IntentParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    validation = validate(patch, state)

    return {
        "patch": patch.model_dump(mode="json") if hasattr(patch, "model_dump") else patch,
        "validation": validation.model_dump(),
        "current_version": state.version,
    }


@router.post("/{dashboard_id}/patch/apply")
async def apply_patch_endpoint(
    workspace_id: str,
    dashboard_id: str,
    body: ApplyRequest,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Apply a patch. Accepts either a raw patch dict OR an NL instruction.
    Syncs to Metabase AFTER apply, then patches back the Metabase IDs
    into the state before saving.
    """
    try:
        async with lock(dashboard_id):
            try:
                await check_conflict(dashboard_id, body.base_version)
            except ConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc))

            state = await state_store.load_latest(dashboard_id)

            # Resolve patch
            if body.patch:
                try:
                    patch = parse_patch(body.patch)
                except Exception as exc:
                    raise HTTPException(status_code=400, detail=f"Invalid patch: {exc}")
            elif body.instruction:
                schema_hint = await _load_schema_hint(workspace_id)
                try:
                    patch = await parse_instruction(
                        body.instruction,
                        state,
                        api_key=ctx.groq_key,
                        redis_prefix=ctx.redis_prefix,
                        schema_hint=schema_hint,
                    )
                except IntentParseError as exc:
                    raise HTTPException(status_code=400, detail=str(exc))
            else:
                raise HTTPException(status_code=400, detail="Need 'patch' or 'instruction'")

            # Validate
            result = validate(patch, state)
            if not result.valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation failed: {result.reason}",
                )

            # Apply to state
            try:
                new_state, actions = apply(state, patch)
            except PatchApplyError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

            # Sync to Metabase first, get back IDs
            metabase_results, refs = await sync_to_metabase(
                new_state.metabase_dashboard_id,
                actions,
            )

            # Patch Metabase IDs back into the new state
            for cid, ref in refs.items():
                card = find_card(new_state, cid)
                if card:
                    if ref.get("mb_card_id"):
                        card.metabase.card_id = ref["mb_card_id"]
                    if ref.get("mb_dashcard_id"):
                        card.metabase.dashcard_id = ref["mb_dashcard_id"]

            # Save version (with Metabase IDs already filled in)
            saved = await state_store.save_version(
                dashboard_id=dashboard_id,
                state=new_state,
                patch=patch,
                user_id=user["id"],
                from_version=state.version,
            )

            logger.info(
                f"[SUCCESS] Patch applied: dashboard={dashboard_id} "
                f"v{state.version} -> v{new_state.version} "
                f"({len(actions)} actions, {len(metabase_results)} mb results)"
            )

            return {
                "version": new_state.version,
                "parent_version": new_state.parent_version,
                "state": new_state.model_dump(mode="json"),
                "actions_count": len(actions),
                "metabase_results": metabase_results,
                "saved_id": saved.get("id"),
            }
    except LockError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    except StateStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{dashboard_id}/patch/reject")
async def reject_patch(
    workspace_id: str,
    dashboard_id: str,
    ctx: WorkspaceContext = Depends(get_workspace_context),
    user: dict = Depends(get_current_user),
) -> dict:
    """Reject a previewed patch (reserved for future preview flow)."""
    return {"rejected": True, "dashboard_id": dashboard_id}