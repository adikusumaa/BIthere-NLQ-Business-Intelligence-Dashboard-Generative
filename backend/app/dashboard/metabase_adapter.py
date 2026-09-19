"""
Metabase Adapter (F-13).
Translates abstract actions from patch_applier into concrete
Metabase API calls. Uses the existing Metabase client service.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import logger


class MetabaseAdapterError(Exception):
    """Raised when a Metabase API call fails."""


class MetabaseSession:
    """Lightweight Metabase session wrapper (login on init)."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session_id: Optional[str] = None

    async def login(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/api/session",
                json={"username": self.username, "password": self.password},
            )
        if response.status_code != 200:
            raise MetabaseAdapterError(
                f"Metabase login failed: {response.status_code} {response.text[:200]}"
            )
        self.session_id = response.json().get("id")
        logger.info("[PROCESS] Metabase session established")
        return self.session_id

    def _headers(self) -> dict:
        if not self.session_id:
            raise MetabaseAdapterError("Not logged in")
        return {
            "X-Metabase-Session": self.session_id,
            "Content-Type": "application/json",
        }

    async def create_card(
        self,
        title: str,
        sql: Optional[str],
        chart_type: str,
        style: Optional[dict] = None,
        database_id: Optional[int] = None,
    ) -> int:
        """Create a Metabase card. Returns card id."""
        if not sql:
            sql = "SELECT 1 AS dummy"

        display_map = {
            "scalar": "scalar",
            "bar": "bar",
            "line": "line",
            "pie": "pie",
            "area": "area",
            "table": "table",
            "text": "text",
        }
        display = display_map.get(chart_type, "table")

        payload = {
            "name": title,
            "display": display,
            "dataset_query": {
                "type": "native",
                "native": {"query": sql, "template-tags": {}},
                "database": database_id or 1,
            },
            "visualization_settings": style or {},
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/api/card",
                headers=self._headers(),
                json=payload,
            )

        if response.status_code not in (200, 201):
            raise MetabaseAdapterError(
                f"create_card failed: {response.status_code} {response.text[:200]}"
            )
        card_id = response.json().get("id")
        logger.info(f"[SUCCESS] Metabase card created: id={card_id}")
        return card_id

    async def update_card(self, card_id: int, updates: dict) -> bool:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/card/{card_id}",
                headers=self._headers(),
                json=updates,
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"update_card failed: {response.status_code} {response.text[:200]}"
            )
        return True

    async def delete_card(self, card_id: int) -> bool:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.delete(
                f"{self.base_url}/api/card/{card_id}",
                headers=self._headers(),
            )
        if response.status_code not in (200, 204):
            raise MetabaseAdapterError(
                f"delete_card failed: {response.status_code}"
            )
        return True

    async def get_dashboard_cards(self, dashboard_id: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._headers(),
            )
        if response.status_code != 200:
            raise MetabaseAdapterError(
                f"get_dashboard failed: {response.status_code}"
            )
        return response.json().get("dashcards", [])

    async def add_card_to_dashboard(
        self,
        dashboard_id: int,
        card_id: int,
        position: dict,
    ) -> int:
        """Add a card to a dashboard. Returns dashcard id."""
        current = await self.get_dashboard_cards(dashboard_id)

        new_dashcard = {
            "id": -1,
            "card_id": card_id,
            "row": position.get("row", 0),
            "col": position.get("col", 0),
            "size_x": position.get("size_x", 6),
            "size_y": position.get("size_y", 3),
            "parameter_mappings": [],
            "visualization_settings": {},
        }

        payload = {"cards": current + [new_dashcard]}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json=payload,
            )

        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"add_card_to_dashboard failed: {response.status_code} {response.text[:200]}"
            )

        updated = await self.get_dashboard_cards(dashboard_id)
        for dc in updated:
            if dc.get("card_id") == card_id:
                return dc.get("id", -1)
        return -1

    async def update_dashcards(self, dashboard_id: int, updates: List[dict]) -> bool:
        """
        Batch-update dashcards (positions, sizes).
        updates: [{"id": <dashcard_id>, "row": ..., "col": ..., "size_x": ..., "size_y": ...}, ...]
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json={"cards": updates},
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"update_dashcards failed: {response.status_code}"
            )
        return True

    async def delete_dashcard(self, dashboard_id: int, dashcard_id: int) -> bool:
        current = await self.get_dashboard_cards(dashboard_id)
        remaining = [c for c in current if c.get("id") != dashcard_id]

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json={"cards": remaining},
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"delete_dashcard failed: {response.status_code}"
            )
        return True

    async def add_filter_to_dashboard(self, dashboard_id: int, filter_spec: dict) -> bool:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._headers(),
            )
        if response.status_code != 200:
            raise MetabaseAdapterError("get_dashboard failed")

        dashboard = response.json()
        params = dashboard.get("parameters", [])
        params.append({
            "id": filter_spec.get("id", ""),
            "name": filter_spec.get("name", "Filter"),
            "slug": filter_spec.get("name", "filter").lower().replace(" ", "_"),
            "type": filter_spec.get("type", "category"),
        })

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._headers(),
                json={"parameters": params},
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"add_filter failed: {response.status_code}"
            )
        return True


# =====================================================
# Adapter: abstract action → Metabase call
# =====================================================

async def execute_actions(
    session: MetabaseSession,
    dashboard_id: int,
    actions: List[Dict[str, Any]],
    database_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a list of abstract actions against Metabase.

    Actions come from patch_applier.apply() and are of form:
      {"action": "...", ...}

    Returns list of {"ok": bool, "action": ..., "result": ..., "error": ...}.
    """
    results: List[Dict[str, Any]] = []

    # Cache for metabase card_id ↔ our card_id mapping
    local_to_mb_card: Dict[str, int] = {}
    local_to_mb_dashcard: Dict[str, int] = {}

    for act in actions:
        action_name = act.get("action")
        try:
            if action_name == "create_card":
                mb_card_id = await session.create_card(
                    title=act["title"],
                    sql=act.get("sql"),
                    chart_type=act.get("chart_type", "table"),
                    style=act.get("style"),
                    database_id=database_id,
                )
                local_to_mb_card[act["card_id"]] = mb_card_id
                results.append({"ok": True, "action": action_name, "result": mb_card_id})

            elif action_name == "attach_card_to_dashboard":
                our_card_id = act["card_id"]
                mb_card_id = local_to_mb_card.get(our_card_id)
                if mb_card_id is None:
                    raise MetabaseAdapterError(f"No Metabase card for {our_card_id}")
                dashcard_id = await session.add_card_to_dashboard(
                    dashboard_id=dashboard_id,
                    card_id=mb_card_id,
                    position=act["position"],
                )
                local_to_mb_dashcard[our_card_id] = dashcard_id
                results.append({"ok": True, "action": action_name, "result": dashcard_id})

            elif action_name == "delete_dashcard":
                dashcard_id = act.get("dashcard_id") or local_to_mb_dashcard.get(act["card_id"])
                if dashcard_id:
                    await session.delete_dashcard(dashboard_id, dashcard_id)
                results.append({"ok": True, "action": action_name})

            elif action_name == "update_dashcard_position":
                dashcard_id = act.get("dashcard_id") or local_to_mb_dashcard.get(act["card_id"])
                if dashcard_id is None:
                    results.append({"ok": False, "action": action_name, "error": "no dashcard id"})
                    continue
                await session.update_dashcards(dashboard_id, [{
                    "id": dashcard_id,
                    **act["position"],
                }])
                results.append({"ok": True, "action": action_name})

            elif action_name == "update_card_style":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(act["card_id"])
                if mb_card_id:
                    await session.update_card(mb_card_id, {
                        "visualization_settings": act.get("style", {}),
                    })
                results.append({"ok": True, "action": action_name})

            elif action_name == "update_card_name":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(act["card_id"])
                if mb_card_id:
                    await session.update_card(mb_card_id, {"name": act["title"]})
                results.append({"ok": True, "action": action_name})

            elif action_name == "update_card_display":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(act["card_id"])
                if mb_card_id:
                    await session.update_card(mb_card_id, {"display": act["display"]})
                results.append({"ok": True, "action": action_name})

            elif action_name == "update_card_sql":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(act["card_id"])
                if mb_card_id:
                    await session.update_card(mb_card_id, {
                        "dataset_query": {
                            "type": "native",
                            "native": {"query": act["sql"], "template-tags": {}},
                            "database": database_id or 1,
                        },
                    })
                results.append({"ok": True, "action": action_name})

            elif action_name == "add_dashboard_filter":
                await session.add_filter_to_dashboard(dashboard_id, act["filter"])
                results.append({"ok": True, "action": action_name})

            elif action_name == "remove_dashboard_filter":
                # Simplified: no-op (filter removal at Metabase needs parameters update)
                results.append({"ok": True, "action": action_name, "note": "no-op"})

            else:
                results.append({"ok": False, "action": action_name, "error": "unknown action"})

        except Exception as exc:
            logger.error(f"[ERROR] Action '{action_name}' failed: {exc}")
            results.append({"ok": False, "action": action_name, "error": str(exc)})

    return results