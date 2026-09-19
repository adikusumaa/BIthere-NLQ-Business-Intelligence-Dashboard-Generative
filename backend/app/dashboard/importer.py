"""
Dashboard importer: convert an existing Metabase dashboard into an F-13
DashboardState so it can be edited with the patch engine.
"""

import uuid
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.dashboard import state_store
from app.dashboard.metabase_adapter import MetabaseSession
from app.dashboard.state_model import (
    Card,
    CardStyle,
    DashboardState,
    MetabaseRef,
    Page,
    Position,
)


class ImportError(Exception):
    """Raised when a Metabase dashboard cannot be imported."""


DISPLAY_TO_TYPE = {
    "scalar": "scalar",
    "smartscalar": "scalar",
    "progress": "scalar",
    "gauge": "scalar",
    "bar": "bar",
    "row": "bar",
    "combo": "bar",
    "waterfall": "bar",
    "funnel": "bar",
    "line": "line",
    "area": "area",
    "pie": "pie",
    "table": "table",
    "text": "text",
}


async def import_from_metabase(
    workspace_id: str,
    metabase_dashboard_id: int,
    user_id: Optional[str] = None,
    name_override: Optional[str] = None,
) -> DashboardState:
    """
    Fetch a Metabase dashboard, convert to DashboardState, persist as v1.
    Returns the newly created DashboardState.
    """
    session = MetabaseSession(
        base_url=settings.METABASE_URL,
        username=settings.METABASE_USERNAME,
        password=settings.METABASE_PASSWORD,
    )

    try:
        await session.login()
    except Exception as exc:
        raise ImportError(f"Cannot login to Metabase: {exc}")

    try:
        dashboard = await _fetch_dashboard(session, metabase_dashboard_id)
    except Exception as exc:
        raise ImportError(f"Cannot fetch dashboard: {exc}")

    dashcards = dashboard.get("dashcards", [])
    if not dashcards:
        raise ImportError(f"Dashboard {metabase_dashboard_id} has no cards")

    cards: List[Card] = []
    for dc in dashcards:
        mb_card_id = dc.get("card_id")
        if not mb_card_id:
            continue

        try:
            card_data = await _fetch_card(session, mb_card_id)
        except Exception as exc:
            logger.warning(f"[WARNING] Skip card {mb_card_id}: {exc}")
            continue

        sql = _extract_sql(card_data)
        display = card_data.get("display", "table")
        card_type = DISPLAY_TO_TYPE.get(display, "table")
        color = _extract_color(card_data.get("visualization_settings") or {})

        cards.append(Card(
            id=f"card-{mb_card_id}",
            title=card_data.get("name", f"Card {mb_card_id}"),
            type=card_type,
            sql=sql,
            position=Position(
                row=dc.get("row", 0),
                col=dc.get("col", 0),
                size_x=dc.get("size_x", 6),
                size_y=dc.get("size_y", 3),
            ),
            style=CardStyle(color=color),
            metabase=MetabaseRef(
                card_id=mb_card_id,
                dashcard_id=dc.get("id"),
            ),
        ))

    if not cards:
        raise ImportError("No usable cards found to import")

    dashboard_id = str(uuid.uuid4())
    state = DashboardState(
        dashboard_id=dashboard_id,
        workspace_id=workspace_id,
        metabase_dashboard_id=metabase_dashboard_id,
        version=1,
        pages=[
            Page(
                id="page-1",
                name=name_override or dashboard.get("name", "Imported Dashboard"),
                cards=cards,
                filters=[],
            ),
        ],
    )

    await state_store.save_version(
        dashboard_id=dashboard_id,
        state=state,
        patch=None,
        user_id=user_id,
    )

    logger.info(
        f"[SUCCESS] Imported Metabase dashboard {metabase_dashboard_id} "
        f"-> F-13 state {dashboard_id} ({len(cards)} cards)"
    )
    return state


async def _fetch_dashboard(session: MetabaseSession, dashboard_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{session.base_url}/api/dashboard/{dashboard_id}",
            headers=session._headers(),
        )
    if response.status_code != 200:
        raise ImportError(
            f"Metabase dashboard fetch failed: {response.status_code} {response.text[:200]}"
        )
    return response.json()


async def _fetch_card(session: MetabaseSession, card_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{session.base_url}/api/card/{card_id}",
            headers=session._headers(),
        )
    if response.status_code != 200:
        raise ImportError(f"Card {card_id} fetch failed: {response.status_code}")
    return response.json()


def _extract_sql(card_data: Dict[str, Any]) -> Optional[str]:
    dq = card_data.get("dataset_query") or {}
    if dq.get("type") != "native":
        return None
    native = dq.get("native") or {}
    return native.get("query")


def _extract_color(viz: Dict[str, Any]) -> Optional[str]:
    series = viz.get("series_settings") or {}
    for _, settings in series.items():
        c = settings.get("color")
        if c:
            return c if c.startswith("#") else f"#{c}"
    return None