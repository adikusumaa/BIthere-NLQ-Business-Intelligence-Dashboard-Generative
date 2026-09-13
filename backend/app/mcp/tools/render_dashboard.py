"""
MCP tool: render_dashboard
Create a Metabase card from a SQL query and embed it in a new dashboard.
"""

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import log_process, log_success, log_error


_session_token: str | None = None

VALID_DISPLAYS = {"table", "bar", "line", "area", "pie", "scalar"}


async def _authenticate() -> str:
    """Login to Metabase, cache session token for reuse."""
    global _session_token
    if _session_token:
        return _session_token

    async with httpx.AsyncClient(
        base_url=settings.METABASE_URL, timeout=30.0
    ) as client:
        response = await client.post(
            "/api/session",
            json={
                "username": settings.METABASE_USERNAME,
                "password": settings.METABASE_PASSWORD,
            },
        )
        response.raise_for_status()
        _session_token = response.json()["id"]
    return _session_token


async def _get_supabase_database_id(
    client: httpx.AsyncClient, headers: dict
) -> int | None:
    """Find the Supabase database ID in Metabase."""
    response = await client.get("/api/database", headers=headers)
    response.raise_for_status()
    databases = response.json().get("data", [])

    for db in databases:
        if "supabase" in db.get("name", "").lower():
            return db["id"]
    return databases[0]["id"] if databases else None


# ---------------------------------------------------------------------
# Multi-card dashboard
# ---------------------------------------------------------------------
# Layout grid: 24 columns wide.
# Each chart specifies (row, col, size_x, size_y).
# ---------------------------------------------------------------------

DEFAULT_LAYOUTS = {
    1: [(0, 0, 24, 8)],
    2: [(0, 0, 12, 8), (0, 12, 12, 8)],
    3: [(0, 0, 8, 8), (0, 8, 8, 8), (0, 16, 8, 8)],
    4: [
        (0, 0, 12, 8), (0, 12, 12, 8),
        (8, 0, 12, 8), (8, 12, 12, 8),
    ],
    5: [
        (0, 0, 6, 8), (0, 6, 18, 8),
        (8, 0, 12, 8), (8, 12, 12, 8),
        (16, 0, 24, 8),
    ],
}


async def render_dashboard_multi(
    title: str,
    charts: list[dict],
) -> dict[str, Any]:
    """
    Create multiple Metabase cards and place them in one dashboard.

    Args:
        title: Dashboard name.
        charts: List of dicts, each with keys:
            - title (str): Card title.
            - sql (str): PostgreSQL SELECT query.
            - display (str): table|bar|line|area|pie|scalar.

    Returns:
        dict: success, dashboard_id, card_ids, embed_url, error.
    """
    log_process(f"render_dashboard_multi: '{title}' with {len(charts)} charts")

    if not charts:
        return _fail("At least one chart is required")

    try:
        async with httpx.AsyncClient(
            base_url=settings.METABASE_URL, timeout=90.0
        ) as client:
            token = await _authenticate()
            headers = {"X-Metabase-Session": token}

            db_id = await _get_supabase_database_id(client, headers)
            if not db_id:
                return _fail("No database found in Metabase")

            dashboard_id = await _create_dashboard(client, headers, title)
            card_ids: list[int] = []

            for chart in charts:
                display = chart.get("display", "table")
                if display not in VALID_DISPLAYS:
                    display = "table"
                card_id = await _create_card(
                    client,
                    headers,
                    db_id,
                    chart["title"],
                    chart["sql"],
                    display,
                )
                card_ids.append(card_id)

            layout = DEFAULT_LAYOUTS.get(len(card_ids), [])
            if not layout:
                layout = [(i * 8, 0, 24, 8) for i in range(len(card_ids))]

            await _add_cards_to_dashboard(
                client, headers, dashboard_id, card_ids, layout
            )
            embed_url = await _enable_public_link(
                client, headers, dashboard_id
            )

            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "card_ids": card_ids,
                "embed_url": embed_url,
                "error": None,
            }

    except httpx.HTTPStatusError as exc:
        log_error(
            f"Metabase HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard_multi failed: {exc}")
        return _fail(str(exc))


async def _add_cards_to_dashboard(
    client: httpx.AsyncClient,
    headers: dict,
    dashboard_id: int,
    card_ids: list[int],
    layout: list[tuple[int, int, int, int]],
) -> None:
    """Add multiple cards to a dashboard with grid layout."""
    dashcards = []
    for idx, (card_id, (row, col, sx, sy)) in enumerate(
        zip(card_ids, layout)
    ):
        dashcards.append(
            {
                "id": -(idx + 1),
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": sx,
                "size_y": sy,
            }
        )

    resp = await client.put(
        f"/api/dashboard/{dashboard_id}",
        headers=headers,
        json={"dashcards": dashcards},
    )
    resp.raise_for_status()
    log_success(f"Added {len(dashcards)} cards to dashboard {dashboard_id}")

def _fail(message: str) -> dict[str, Any]:
    return {
        "success": False,
        "card_id": None,
        "dashboard_id": None,
        "embed_url": None,
        "error": message,
    }


async def _create_card(
    client: httpx.AsyncClient,
    headers: dict,
    db_id: int,
    title: str,
    sql_query: str,
    display: str,
) -> int:
    payload = {
        "name": title,
        "dataset_query": {
            "type": "native",
            "native": {"query": sql_query},
            "database": db_id,
        },
        "display": display,
        "visualization_settings": {},
    }
    resp = await client.post("/api/card", headers=headers, json=payload)
    resp.raise_for_status()
    card_id = resp.json()["id"]
    log_success(f"Card created: id={card_id}")
    return card_id


async def _create_dashboard(
    client: httpx.AsyncClient, headers: dict, title: str
) -> int:
    resp = await client.post(
        "/api/dashboard", headers=headers, json={"name": title}
    )
    resp.raise_for_status()
    dashboard_id = resp.json()["id"]
    log_success(f"Dashboard created: id={dashboard_id}")
    return dashboard_id


async def _add_card_to_dashboard(
    client: httpx.AsyncClient,
    headers: dict,
    dashboard_id: int,
    card_id: int,
) -> None:
    payload = {
        "dashcards": [
            {
                "id": -1,
                "card_id": card_id,
                "row": 0,
                "col": 0,
                "size_x": 12,
                "size_y": 8,
            }
        ]
    }
    resp = await client.put(
        f"/api/dashboard/{dashboard_id}", headers=headers, json=payload
    )
    resp.raise_for_status()
    log_success(f"Card {card_id} added to dashboard {dashboard_id}")


async def _enable_public_link(
    client: httpx.AsyncClient, headers: dict, dashboard_id: int
) -> str:
    fallback = f"{settings.METABASE_URL}/dashboard/{dashboard_id}"
    try:
        resp = await client.post(
            f"/api/dashboard/{dashboard_id}/public_link", headers=headers
        )
        if resp.status_code == 200:
            uuid = resp.json().get("uuid")
            if uuid:
                url = f"{settings.METABASE_URL}/public/dashboard/{uuid}"
                log_success(f"Public link enabled: {url}")
                return url
    except Exception as exc:
        log_error(f"Public link failed: {exc}")

    log_process("Falling back to internal dashboard URL")
    return fallback