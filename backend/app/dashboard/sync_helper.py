"""
Shared helper: execute abstract actions against Metabase and return
both per-action results and a mapping of local card_id -> Metabase IDs.
"""

from typing import Any, Dict, List, Tuple

from app.core.config import settings
from app.core.logging import logger


async def sync_to_metabase(
    metabase_dashboard_id: int | None,
    actions: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    """
    Execute abstract actions against Metabase.

    Returns:
        (results, refs) where refs maps local card_id to
        {"mb_card_id": int, "mb_dashcard_id": int}.
    """
    if not metabase_dashboard_id or not actions:
        return [], {}

    try:
        from app.dashboard.metabase_adapter import MetabaseSession, execute_actions

        session = MetabaseSession(
            base_url=settings.METABASE_URL,
            username=settings.METABASE_USERNAME,
            password=settings.METABASE_PASSWORD,
        )
        await session.login()

        results = await execute_actions(
            session,
            dashboard_id=metabase_dashboard_id,
            actions=actions,
        )

        refs: Dict[str, Dict[str, int]] = {}
        for r in results:
            if not r.get("ok"):
                continue
            cid = r.get("card_id")
            if not cid:
                continue
            action = r.get("action")
            result_val = r.get("result")
            if action == "create_card" and isinstance(result_val, int):
                refs.setdefault(cid, {})["mb_card_id"] = result_val
            elif action == "attach_card_to_dashboard" and isinstance(result_val, int):
                refs.setdefault(cid, {})["mb_dashcard_id"] = result_val

        ok_count = sum(1 for r in results if r.get("ok"))
        logger.info(
            f"[SUCCESS] Metabase sync: {len(actions)} actions -> {ok_count} ok"
        )
        return results, refs
    except Exception as exc:
        logger.error(f"[ERROR] Metabase sync failed: {exc}")
        return [{"ok": False, "error": str(exc)}], {}