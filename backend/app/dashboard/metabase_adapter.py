"""
Metabase Adapter (F-13).
Translates abstract actions from patch_applier into concrete Metabase API calls.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.core.logging import logger


class MetabaseAdapterError(Exception):
    """Raised when a Metabase API call fails."""


class MetabaseSession:
    """Lightweight Metabase session wrapper (login on init)."""
    async def get_default_database_id(self) -> int:
        """Fetch the first database ID from Metabase."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/api/database",
                headers=self._headers(),
            )
        if response.status_code != 200:
            return 1
        dbs = response.json().get("data", [])
        for db in dbs:
            if "sample" not in (db.get("name") or "").lower():
                return db.get("id", 1)
        return dbs[0].get("id", 1) if dbs else 1

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session_id: Optional[str] = None
        self._default_tab_id: Optional[int] = None

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
        if not sql:
            sql = "SELECT 1 AS dummy"

        if not database_id:
            database_id = await self.get_default_database_id()

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

    async def get_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._headers(),
            )
        if response.status_code != 200:
            raise MetabaseAdapterError(
                f"get_dashboard failed: {response.status_code}"
            )
        return response.json()

    async def get_dashboard_cards(self, dashboard_id: int) -> List[Dict[str, Any]]:
        dashboard = await self.get_dashboard(dashboard_id)
        return dashboard.get("dashcards", [])

    async def get_default_tab_id(self, dashboard_id: int) -> Optional[int]:
        """Return the first tab id, or None if the dashboard has no tabs."""
        if self._default_tab_id is not None:
            return self._default_tab_id
        dashboard = await self.get_dashboard(dashboard_id)
        tabs = dashboard.get("tabs") or []
        if tabs:
            self._default_tab_id = tabs[0].get("id")
        return self._default_tab_id

    async def add_card_to_dashboard(
        self,
        dashboard_id: int,
        card_id: int,
        position: dict,
    ) -> int:
        """Add a card to a dashboard. Preserves tabs and existing dashcards."""
        dashboard = await self.get_dashboard(dashboard_id)
        current_dashcards = dashboard.get("dashcards", [])
        tabs = dashboard.get("tabs", []) or []

        tab_id = tabs[0].get("id") if tabs else None

        new_dc: Dict[str, Any] = {
            "id": -1,
            "card_id": card_id,
            "row": position.get("row", 0),
            "col": position.get("col", 0),
            "size_x": position.get("size_x", 6),
            "size_y": position.get("size_y", 3),
            "parameter_mappings": [],
            "visualization_settings": {},
        }
        if tab_id is not None:
            new_dc["dashboard_tab_id"] = tab_id

        cards: List[Dict[str, Any]] = []
        for dc in current_dashcards:
            c = dict(dc)
            if tab_id is not None and not c.get("dashboard_tab_id"):
                c["dashboard_tab_id"] = tab_id
            cards.append(c)
        cards.append(new_dc)

        payload: Dict[str, Any] = {"cards": cards}
        if tabs:
            payload["tabs"] = tabs

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json=payload,
            )

        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"add_card_to_dashboard failed: {response.status_code} {response.text[:300]}"
            )

        updated = await self.get_dashboard_cards(dashboard_id)
        for dc in updated:
            if dc.get("card_id") == card_id:
                return dc.get("id", -1)
        return -1

    async def update_dashcards(self, dashboard_id: int, updates: List[dict]) -> bool:
        """Batch-update dashcards. Preserves tabs and all existing fields."""
        dashboard = await self.get_dashboard(dashboard_id)
        current = dashboard.get("dashcards", [])
        tabs = dashboard.get("tabs", []) or []

        tab_id = tabs[0].get("id") if tabs else None

        by_id = {dc.get("id"): dict(dc) for dc in current}

        for upd in updates:
            dashcard_id = upd.get("id")
            if dashcard_id and dashcard_id in by_id:
                by_id[dashcard_id].update(upd)
                if tab_id is not None and not by_id[dashcard_id].get("dashboard_tab_id"):
                    by_id[dashcard_id]["dashboard_tab_id"] = tab_id

        merged = list(by_id.values())

        payload: Dict[str, Any] = {"cards": merged}
        if tabs:
            payload["tabs"] = tabs

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json=payload,
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"update_dashcards failed: {response.status_code} {response.text[:300]}"
            )
        return True

    async def delete_dashcard(self, dashboard_id: int, dashcard_id: int) -> bool:
        current = await self.get_dashboard_cards(dashboard_id)
        remaining = [dc for dc in current if dc.get("id") != dashcard_id]

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                f"{self.base_url}/api/dashboard/{dashboard_id}/cards",
                headers=self._headers(),
                json={"cards": remaining},
            )
        if response.status_code not in (200, 202):
            raise MetabaseAdapterError(
                f"delete_dashcard failed: {response.status_code} {response.text[:200]}"
            )
        return True

    async def add_filter_to_dashboard(self, dashboard_id: int, filter_spec: dict) -> bool:
        dashboard = await self.get_dashboard(dashboard_id)
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
# Adapter: abstract action -> Metabase call
# =====================================================

async def execute_actions(
    session: MetabaseSession,
    dashboard_id: int,
    actions: List[Dict[str, Any]],
    database_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    local_to_mb_card: Dict[str, int] = {}
    local_to_mb_dashcard: Dict[str, int] = {}

    for act in actions:
        action_name = act.get("action")
        local_card_id = act.get("card_id")
        try:
            if action_name == "create_card":
                mb_card_id = await session.create_card(
                    title=act["title"],
                    sql=act.get("sql"),
                    chart_type=act.get("chart_type", "table"),
                    style=act.get("style"),
                    database_id=database_id,
                )
                local_to_mb_card[local_card_id] = mb_card_id
                results.append({
                    "ok": True,
                    "action": action_name,
                    "card_id": local_card_id,
                    "result": mb_card_id,
                })

            elif action_name == "attach_card_to_dashboard":
                mb_card_id = local_to_mb_card.get(local_card_id)
                if mb_card_id is None:
                    raise MetabaseAdapterError(f"No Metabase card for {local_card_id}")
                dashcard_id = await session.add_card_to_dashboard(
                    dashboard_id=dashboard_id,
                    card_id=mb_card_id,
                    position=act["position"],
                )
                local_to_mb_dashcard[local_card_id] = dashcard_id
                results.append({
                    "ok": True,
                    "action": action_name,
                    "card_id": local_card_id,
                    "result": dashcard_id,
                })

            elif action_name == "delete_dashcard":
                dashcard_id = act.get("dashcard_id") or local_to_mb_dashcard.get(local_card_id)
                if dashcard_id:
                    await session.delete_dashcard(dashboard_id, dashcard_id)
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "update_dashcard_position":
                dashcard_id = act.get("dashcard_id") or local_to_mb_dashcard.get(local_card_id)
                if dashcard_id is None:
                    results.append({
                        "ok": False,
                        "action": action_name,
                        "card_id": local_card_id,
                        "error": "no dashcard id",
                    })
                    continue
                await session.update_dashcards(dashboard_id, [{
                    "id": dashcard_id,
                    **act["position"],
                }])
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "update_card_style":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(local_card_id)
                if mb_card_id:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        card_resp = await client.get(
                            f"{session.base_url}/api/card/{mb_card_id}",
                            headers=session._headers(),
                        )
                    existing_viz = {}
                    existing_display = None
                    if card_resp.status_code == 200:
                        cd = card_resp.json()
                        existing_viz = dict(cd.get("visualization_settings") or {})
                        existing_display = cd.get("display")

                    new_color = (act.get("style") or {}).get("color")
                    if new_color:
                        series = existing_viz.get("series_settings") or {}
                        if not series:
                            series = {"__default__": {}}
                        for key in series:
                            if isinstance(series[key], dict):
                                series[key]["color"] = new_color
                        existing_viz["series_settings"] = series
                        existing_viz["graph.colors"] = [new_color]

                    update_payload = {"visualization_settings": existing_viz}
                    if existing_display:
                        update_payload["display"] = existing_display

                    await session.update_card(mb_card_id, update_payload)
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "update_card_name":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(local_card_id)
                if mb_card_id:
                    await session.update_card(mb_card_id, {"name": act["title"]})
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "update_card_display":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(local_card_id)
                if mb_card_id:
                    await session.update_card(mb_card_id, {"display": act["display"]})
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "update_card_sql":
                mb_card_id = act.get("metabase_card_id") or local_to_mb_card.get(local_card_id)
                if mb_card_id:
                    db_id = database_id or await session.get_default_database_id()
                    await session.update_card(mb_card_id, {
                        "dataset_query": {
                            "type": "native",
                            "native": {"query": act["sql"], "template-tags": {}},
                            "database": db_id,
                        },
                    })
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "add_dashboard_filter":
                await session.add_filter_to_dashboard(dashboard_id, act["filter"])
                results.append({"ok": True, "action": action_name, "card_id": local_card_id})

            elif action_name == "remove_dashboard_filter":
                results.append({"ok": True, "action": action_name, "note": "no-op"})

            else:
                results.append({
                    "ok": False,
                    "action": action_name,
                    "card_id": local_card_id,
                    "error": "unknown action",
                })

        except Exception as exc:
            logger.error(f"[ERROR] Action '{action_name}' failed: {exc}")
            results.append({
                "ok": False,
                "action": action_name,
                "card_id": local_card_id,
                "error": str(exc),
            })

    return results