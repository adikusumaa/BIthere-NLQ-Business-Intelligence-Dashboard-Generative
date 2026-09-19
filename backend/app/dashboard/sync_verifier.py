"""
Sync verifier: compare local state vs Metabase (light check).
"""

from typing import Any, Dict, List

from app.core.logging import logger
from app.dashboard.metabase_adapter import MetabaseSession
from app.dashboard.state_model import DashboardState


async def verify_sync(
    state: DashboardState,
    session: MetabaseSession,
    dashboard_id: int,
) -> Dict[str, Any]:
    """
    Compare the local state cards vs Metabase dashcards.
    Returns a report with matching/missing/extra card ids.
    """
    try:
        dashcards = await session.get_dashboard_cards(dashboard_id)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    mb_card_ids = {dc.get("card_id") for dc in dashcards if dc.get("card_id")}
    local_card_ids = set()
    for page in state.pages:
        for card in page.cards:
            if card.metabase.card_id:
                local_card_ids.add(card.metabase.card_id)

    missing_in_mb = local_card_ids - mb_card_ids
    extra_in_mb = mb_card_ids - local_card_ids

    ok = not missing_in_mb and not extra_in_mb
    if not ok:
        logger.warning(
            f"[WARNING] Sync mismatch: missing={missing_in_mb} extra={extra_in_mb}"
        )
    else:
        logger.info("[SUCCESS] Metabase sync verified")

    return {
        "ok": ok,
        "missing_in_metabase": list(missing_in_mb),
        "extra_in_metabase": list(extra_in_mb),
        "local_count": len(local_card_ids),
        "metabase_count": len(mb_card_ids),
    }