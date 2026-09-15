"""
MCP tool: render_dashboard
Create Metabase cards from SQL queries and embed them in dashboards.

Supported modes:
1. render_dashboard            - single card dashboard
2. render_dashboard_multi      - multiple cards, single page
3. render_dashboard_pages      - multi-page dashboard with tabs
4. render_dashboard_interactive - multi-page with variable filters
5. render_dashboard_dynamic    - config-driven single or multi-page dashboard

Filter convention (basic variables, reliable with multi-table JOINs):
    text   ->  [[AND alias.column = {{tag}}]]
    number ->  [[AND alias.column = {{tag}}]]
    date   ->  [[AND alias.column = {{tag}}]]
Metabase adds quotes automatically for text variables.
The [[ ]] block is dropped by Metabase when the filter is empty.

Cross-filter highlight:
    Charts that drive a filter also get a parameter_mapping to that filter
    (even if the tag is not referenced in their SQL). This makes Metabase
    keep the bold/fade highlight on the selected bar persistently.
"""

import re
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import (
    log_process, log_success, log_error, log_warning, log_info,
)

_session_token: str | None = None


VALID_DISPLAYS = {
    "table", "bar", "bar/stacked", "row", "row/stacked",
    "line", "area", "area/stacked", "combo",
    "pie", "donut", "scalar", "smartscalar",
    "gauge", "progress", "funnel", "scatter", "waterfall", "map",
}

PARAM_TYPE_BY_SECTION = {
    "string": "string/=",
    "category": "string/=",
    "location/state": "string/=",
    "location/city": "string/=",
    "number": "number/=",
    "date": "date/single",
}

TAG_TYPE_BY_SECTION = {
    "string": "text",
    "category": "text",
    "location/state": "text",
    "location/city": "text",
    "number": "number",
    "date": "date",
}


async def _authenticate() -> str:
    """Login to Metabase and cache the session token."""
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
    """Locate the Supabase database in Metabase by name."""
    response = await client.get("/api/database", headers=headers)
    response.raise_for_status()
    databases = response.json().get("data", [])
    for db in databases:
        if "supabase" in db.get("name", "").lower():
            return db["id"]
    return databases[0]["id"] if databases else None


def _fail(message: str) -> dict[str, Any]:
    """Standard failure response."""
    return {
        "success": False,
        "card_id": None,
        "dashboard_id": None,
        "embed_url": None,
        "error": message,
    }


def _build_variable_tag(name: str, display_name: str, var_type: str) -> dict:
    """Build a basic variable template tag (text / number / date)."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "display-name": display_name,
        "type": var_type,
    }


def _strip_alias_prefix(col: str | None) -> str | None:
    """Remove the table alias prefix from a column reference."""
    if not col:
        return col
    return col.split(".")[-1] if "." in col else col


def _infer_dimension_metric_from_sql(sql: str) -> tuple[str | None, str | None]:
    """Infer dimension and metric column names from SQL SELECT aliases."""
    if not sql:
        return None, None
    match = re.search(
        r"SELECT\s+(.*?)\s+FROM\s",
        sql,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None, None

    select_clause = match.group(1)
    parts: list[str] = []
    depth = 0
    current = ""
    for ch in select_clause:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    agg_pattern = re.compile(
        r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(",
        re.IGNORECASE,
    )

    metric_col: str | None = None
    dim_col: str | None = None

    for part in parts:
        alias_match = re.search(
            r"\s+AS\s+([A-Za-z_][A-Za-z0-9_]*)",
            part,
            re.IGNORECASE,
        )
        if alias_match:
            alias = alias_match.group(1)
        else:
            alias = part.strip().split()[-1] if part.strip() else None

        if not alias:
            continue

        alias = _strip_alias_prefix(alias)

        if agg_pattern.search(part):
            if metric_col is None:
                metric_col = alias
        else:
            if dim_col is None:
                dim_col = alias

    return dim_col, metric_col


def _validate_and_fix_dim_met(
    dimension: str | None,
    metric: str | None,
    sql: str | None,
) -> tuple[str | None, str | None]:
    """
    Validate LLM-provided dimension/metric against the actual SQL.

    If a value does not appear in the SQL, fall back to values inferred
    directly from the SELECT clause.
    """
    inferred_dim, inferred_met = _infer_dimension_metric_from_sql(sql or "")
    sql_lower = (sql or "").lower()

    fixed_dim: str | None = None
    if dimension:
        stripped = _strip_alias_prefix(dimension)
        if stripped and stripped.lower() in sql_lower:
            fixed_dim = stripped
        else:
            log_warning(
                f"dimension '{dimension}' not in SQL; using inferred '{inferred_dim}'"
            )
            fixed_dim = inferred_dim
    else:
        fixed_dim = inferred_dim

    fixed_met: str | None = None
    if metric:
        stripped = _strip_alias_prefix(metric)
        if stripped and stripped.lower() in sql_lower:
            fixed_met = stripped
        else:
            log_warning(
                f"metric '{metric}' not in SQL; using inferred '{inferred_met}'"
            )
            fixed_met = inferred_met
    else:
        fixed_met = inferred_met

    return fixed_dim, fixed_met


def _visualization_defaults(
    display: str,
    dimension: str | None,
    metric: str | None,
    sql: str | None = None,
) -> dict:
    """Provide sensible default visualization_settings per display type."""
    dimension, metric = _validate_and_fix_dim_met(dimension, metric, sql)

    if display in (
        "bar", "bar/stacked", "row", "row/stacked",
        "line", "area", "area/stacked", "combo",
    ):
        s: dict[str, Any] = {}
        if dimension:
            s["graph.dimensions"] = [dimension]
        if metric:
            s["graph.metrics"] = [metric]
        return s

    if display == "map":
        s = {}
        if dimension:
            s["map.dimension_column"] = dimension
        if metric:
            s["map.metric_column"] = metric
        s["map.type"] = "region"
        s["map.region"] = "us_states"
        s["map.colors"] = [
            "#F0F9FF",
            "#BAE6FD",
            "#7DD3FC",
            "#38BDF8",
            "#0EA5E9",
            "#0284C7",
            "#0369A1",
            "#075985",
            "#0C4A6E",
        ]
        return s

    if display in ("pie", "donut"):
        s = {}
        if dimension:
            s["pie.dimension"] = dimension
            s["graph.dimensions"] = [dimension]
        if metric:
            s["pie.metric"] = metric
            s["graph.metrics"] = [metric]
        return s

    if display == "funnel":
        s = {}
        if dimension:
            s["funnel.dimension"] = dimension
        if metric:
            s["funnel.metric"] = metric
        return s

    if display == "progress":
        s = {}
        if dimension:
            s["progress.dimension"] = dimension
        if metric:
            s["progress.metric"] = metric
        return s

    if display == "waterfall":
        s = {}
        if dimension:
            s["waterfall.dimension"] = dimension
        if metric:
            s["waterfall.metric"] = metric
        return s

    if display == "scatter":
        s = {}
        if dimension:
            s["scatter.dimension"] = dimension
        if metric:
            s["scatter.metric"] = metric
        return s

    if display == "smartscalar":
        s = {}
        if metric:
            s["scalar.field"] = metric
        return s

    return {}


def _build_crossfilter_behavior(
    dashboard_param_id: str,
    source_column_name: str,
) -> dict:
    """Build a cross-filter click behavior that updates a dashboard parameter."""
    return {
        "type": "crossfilter",
        "parameterMapping": {
            dashboard_param_id: {
                "id": dashboard_param_id,
                "source": {
                    "type": "column",
                    "id": source_column_name,
                    "name": source_column_name,
                },
                "target": {
                    "type": "parameter",
                    "id": dashboard_param_id,
                },
            }
        },
    }


async def _create_card(
    client: httpx.AsyncClient,
    headers: dict,
    db_id: int,
    title: str,
    sql_query: str,
    display: str,
    template_tags: dict | None = None,
    visualization_settings: dict | None = None,
) -> int:
    """Create a Metabase card with optional template tags and visualization settings."""
    native_query: dict[str, Any] = {"query": sql_query}
    if template_tags:
        native_query["template-tags"] = template_tags

    payload = {
        "name": title,
        "dataset_query": {
            "type": "native",
            "native": native_query,
            "database": db_id,
        },
        "display": display,
        "visualization_settings": visualization_settings or {},
    }
    resp = await client.post("/api/card", headers=headers, json=payload)
    if resp.status_code >= 400:
        log_error(
            f"Card '{title[:40]}' failed: "
            f"{resp.status_code} {resp.text[:300]}"
        )
    resp.raise_for_status()
    card_id = resp.json()["id"]
    log_success(f"Card created: id={card_id} - {title[:40]}")
    return card_id


async def _create_dashboard(
    client: httpx.AsyncClient,
    headers: dict,
    title: str,
    description: str | None = None,
) -> int:
    """Create an empty Metabase dashboard."""
    payload: dict[str, Any] = {"name": title}
    if description:
        payload["description"] = description
    resp = await client.post(
        "/api/dashboard", headers=headers, json=payload
    )
    resp.raise_for_status()
    dashboard_id = resp.json()["id"]
    log_success(f"Dashboard created: id={dashboard_id}")
    return dashboard_id


async def _enable_public_link(
    client: httpx.AsyncClient, headers: dict, dashboard_id: int
) -> str:
    """Enable public sharing and return the public URL."""
    public_base = getattr(settings, "METABASE_PUBLIC_URL", None) or settings.METABASE_URL
    fallback = f"{public_base}/dashboard/{dashboard_id}"

    try:
        resp = await client.post(
            f"/api/dashboard/{dashboard_id}/public_link", headers=headers
        )
        if resp.status_code == 200:
            uuid_value = resp.json().get("uuid")
            if uuid_value:
                url = f"{public_base}/public/dashboard/{uuid_value}"
                log_success(f"Public link enabled: {url}")
                return url
    except Exception as exc:
        log_error(f"Public link failed: {exc}")

    log_process("Falling back to internal dashboard URL")
    return fallback


async def _add_card_to_dashboard(
    client: httpx.AsyncClient,
    headers: dict,
    dashboard_id: int,
    card_id: int,
) -> None:
    """Add a single card to a dashboard in full width."""
    payload = {
        "dashcards": [
            {
                "id": -1,
                "card_id": card_id,
                "row": 0,
                "col": 0,
                "size_x": 24,
                "size_y": 8,
                "parameter_mappings": [],
                "visualization_settings": {},
            }
        ]
    }
    resp = await client.put(
        f"/api/dashboard/{dashboard_id}", headers=headers, json=payload
    )
    resp.raise_for_status()
    log_success(f"Card {card_id} added to dashboard {dashboard_id}")


async def render_dashboard(
    title: str,
    sql_query: str,
    display: str = "table",
) -> dict[str, Any]:
    """Create a single-card dashboard."""
    log_process(f"render_dashboard: '{title[:40]}' ({display})")

    if not title or not title.strip():
        return _fail("Title is required")
    if not sql_query or not sql_query.strip():
        return _fail("SQL query is required")
    if display not in VALID_DISPLAYS:
        display = "table"

    try:
        async with httpx.AsyncClient(
            base_url=settings.METABASE_URL, timeout=60.0
        ) as client:
            token = await _authenticate()
            headers = {"X-Metabase-Session": token}

            db_id = await _get_supabase_database_id(client, headers)
            if not db_id:
                return _fail("No database found in Metabase")

            card_id = await _create_card(
                client, headers, db_id, title, sql_query, display
            )
            dashboard_id = await _create_dashboard(client, headers, title)
            await _add_card_to_dashboard(
                client, headers, dashboard_id, card_id
            )
            embed_url = await _enable_public_link(
                client, headers, dashboard_id
            )

            return {
                "success": True,
                "card_id": card_id,
                "dashboard_id": dashboard_id,
                "embed_url": embed_url,
                "error": None,
            }

    except httpx.HTTPStatusError as exc:
        log_error(
            f"Metabase HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard failed: {exc}")
        return _fail(str(exc))


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


async def _add_cards_to_dashboard(
    client: httpx.AsyncClient,
    headers: dict,
    dashboard_id: int,
    card_ids: list[int],
    layout: list[tuple[int, int, int, int]],
) -> None:
    """Add multiple cards with grid layout to a dashboard."""
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
                "parameter_mappings": [],
                "visualization_settings": {},
            }
        )

    resp = await client.put(
        f"/api/dashboard/{dashboard_id}",
        headers=headers,
        json={"dashcards": dashcards},
    )
    resp.raise_for_status()
    log_success(f"Added {len(dashcards)} cards to dashboard {dashboard_id}")


async def render_dashboard_multi(
    title: str,
    charts: list[dict],
) -> dict[str, Any]:
    """Create multiple cards on a single-page dashboard."""
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

                viz = dict(chart.get("visualization_settings", {}))
                if not viz:
                    viz = _visualization_defaults(
                        display,
                        chart.get("dimension"),
                        chart.get("metric"),
                        chart.get("sql"),
                    )

                card_id = await _create_card(
                    client, headers, db_id,
                    chart["title"], chart["sql"], display,
                    chart.get("template_tags"),
                    viz,
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
            f"Metabase HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard_multi failed: {exc}")
        return _fail(str(exc))


PAGE_LAYOUT = {
    "scalar":    (0, 0, 6, 4),
    "scalar2":   (0, 6, 6, 4),
    "scalar3":   (0, 12, 6, 4),
    "scalar4":   (0, 18, 6, 4),
    "bar":       (0, 0, 12, 8),
    "line":      (0, 12, 12, 8),
    "pie":       (0, 0, 12, 8),
    "table":     (0, 12, 12, 8),
    "half":      (0, 0, 12, 8),
    "half2":     (0, 12, 12, 8),
    "half3":     (8, 0, 12, 8),
    "half4":     (8, 12, 12, 8),
    "third1":    (0, 0, 8, 8),
    "third2":    (0, 8, 8, 8),
    "third3":    (0, 16, 8, 8),
    "third4":    (8, 0, 8, 8),
    "third5":    (8, 8, 8, 8),
    "third6":    (8, 16, 8, 8),
    "quarter1":  (0, 0, 6, 8),
    "quarter2":  (0, 6, 6, 8),
    "quarter3":  (0, 12, 6, 8),
    "quarter4":  (0, 18, 6, 8),
    "quarter5":  (8, 0, 6, 8),
    "quarter6":  (8, 6, 6, 8),
    "quarter7":  (8, 12, 6, 8),
    "quarter8":  (8, 18, 6, 8),
    "full":      (0, 0, 24, 8),
    "wide":      (0, 0, 24, 10),
    "tall":      (0, 0, 12, 12),
    "big":       (0, 0, 24, 14),
    "nextfull":  (8, 0, 24, 8),
    "nextwide":  (10, 0, 24, 10),
}


def _resolve_layout(layout: Any) -> tuple[int, int, int, int]:
    """Accept either a preset layout name or an explicit (row, col, x, y) tuple."""
    if isinstance(layout, (list, tuple)) and len(layout) == 4:
        return tuple(layout)  # type: ignore[return-value]
    if isinstance(layout, str):
        return PAGE_LAYOUT.get(layout, PAGE_LAYOUT["full"])
    return PAGE_LAYOUT["full"]


async def render_dashboard_pages(
    title: str,
    pages: list[dict],
) -> dict[str, Any]:
    """Create a multi-page dashboard with tabs (no filters)."""
    log_process(f"render_dashboard_pages: '{title}' with {len(pages)} pages")

    if not pages:
        return _fail("At least one page is required")

    try:
        async with httpx.AsyncClient(
            base_url=settings.METABASE_URL, timeout=180.0
        ) as client:
            token = await _authenticate()
            headers = {"X-Metabase-Session": token}

            db_id = await _get_supabase_database_id(client, headers)
            if not db_id:
                return _fail("No database found in Metabase")

            dashboard_id = await _create_dashboard(client, headers, title)

            tabs_payload: list[dict] = []
            dashcards_payload: list[dict] = []
            card_ids: list[int] = []
            dashcard_id = -1

            for tab_idx, page in enumerate(pages):
                tab_id = -(tab_idx + 1)
                tabs_payload.append({"id": tab_id, "name": page["name"]})

                for chart in page["charts"]:
                    display = chart.get("display", "table")
                    if display not in VALID_DISPLAYS:
                        display = "table"

                    viz = dict(chart.get("visualization_settings", {}))
                    if not viz:
                        viz = _visualization_defaults(
                            display,
                            chart.get("dimension"),
                            chart.get("metric"),
                            chart.get("sql"),
                        )

                    card_id = await _create_card(
                        client, headers, db_id,
                        chart["title"], chart["sql"], display,
                        chart.get("template_tags"),
                        viz,
                    )
                    card_ids.append(card_id)

                    row, col, sx, sy = _resolve_layout(
                        chart.get("layout", "full")
                    )

                    dashcards_payload.append({
                        "id": dashcard_id,
                        "card_id": card_id,
                        "dashboard_tab_id": tab_id,
                        "row": row,
                        "col": col,
                        "size_x": sx,
                        "size_y": sy,
                        "parameter_mappings": [],
                        "visualization_settings": {},
                    })
                    dashcard_id -= 1

            resp = await client.put(
                f"/api/dashboard/{dashboard_id}",
                headers=headers,
                json={"tabs": tabs_payload, "dashcards": dashcards_payload},
            )
            resp.raise_for_status()
            log_success(
                f"Dashboard {dashboard_id} built with "
                f"{len(tabs_payload)} tabs, {len(card_ids)} cards"
            )

            embed_url = await _enable_public_link(
                client, headers, dashboard_id
            )

            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "card_ids": card_ids,
                "tabs": [p["name"] for p in pages],
                "embed_url": embed_url,
                "error": None,
            }

    except httpx.HTTPStatusError as exc:
        log_error(
            f"Metabase HTTP {exc.response.status_code}: "
            f"{exc.response.text[:300]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard_pages failed: {exc}")
        return _fail(str(exc))

def _extract_conflict_id(error_text: str) -> int | None:
    """Extract the conflicting dashboard ID from a Metabase error."""
    match = re.search(r"key:(\d+)", error_text or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None

def _extract_conflict_id(error_text: str) -> int | None:
    """Extract the conflicting dashboard ID from a Metabase error."""
    match = re.search(r"key:(\d+)", error_text or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None

async def render_dashboard_dynamic(config: dict) -> dict[str, Any]:
    """
    Render a dashboard config — single-page or multi-page.

    Config keys:
        title, description
        filters: list
        charts OR pages:
            - "charts" for single-page
            - "pages"  for multi-page (each page has name + charts)

    Uses BASIC VARIABLES (text/number/date) not Field Filters.
    """
    log_process(
        f"render_dashboard_dynamic: '{config.get('title', '')[:40]}' "
        f"pages={len(config.get('pages', []))} "
        f"charts={len(config.get('charts', []))} "
        f"filters={len(config.get('filters', []))}"
    )

    pages = config.get("pages")
    single_charts = config.get("charts")

    if not pages and not single_charts:
        return _fail("Either charts or pages must be provided")

    title = config.get("title", "Untitled Dashboard")
    description = config.get("description")

    try:
        async with httpx.AsyncClient(
            base_url=settings.METABASE_URL, timeout=300.0
        ) as client:
            token = await _authenticate()
            headers = {"X-Metabase-Session": token}

            db_id = await _get_supabase_database_id(client, headers)
            if not db_id:
                return _fail("No database found in Metabase")

            filter_payload: list[dict] = []
            filter_by_tag: dict[str, dict] = {}
            tag_to_filter_config: dict[str, dict] = {}

            for filt in config.get("filters", []):
                param_type = PARAM_TYPE_BY_SECTION.get(
                    filt["section"], "string/="
                )
                parameter: dict[str, Any] = {
                    "id": str(uuid.uuid4()),
                    "name": filt["name"],
                    "slug": filt["slug"],
                    "type": param_type,
                    "sectionId": filt["section"],
                }

                values = filt.get("values")
                if values and isinstance(values, list):
                    parameter["values_source_type"] = "static-list"
                    parameter["values_source_config"] = {"values": values}

                filter_payload.append(parameter)
                filter_by_tag[filt["target_tag"]] = parameter
                tag_to_filter_config[filt["target_tag"]] = filt

            dashboard_id = await _create_dashboard(
                client, headers, title, description
            )

            tabs_payload: list[dict] = []
            dashcards_payload: list[dict] = []
            card_ids: list[int] = []
            dashcard_id = -1

            if pages:
                work_pages = pages
            else:
                work_pages = [{"name": "Main", "charts": single_charts}]

            for tab_idx, page in enumerate(work_pages):
                tab_id = -(tab_idx + 1)
                if pages:
                    tabs_payload.append({"id": tab_id, "name": page["name"]})

                for chart in page["charts"]:
                    display = chart.get("display", "table")
                    if display not in VALID_DISPLAYS:
                        display = "table"

                    chart_sql = chart["sql"]
                    log_info(
                        f"chart='{chart['title'][:40]}' "
                        f"display={display} "
                        f"dim_in={chart.get('dimension')} "
                        f"met_in={chart.get('metric')}"
                    )
                    template_tags: dict = dict(chart.get("template_tags", {}))
                    used_tag_names: list[str] = []

                    for tag_name, filt in tag_to_filter_config.items():
                        marker = "{{" + tag_name + "}}"
                        if marker not in chart_sql:
                            continue
                        if tag_name in template_tags:
                            used_tag_names.append(tag_name)
                            continue

                        var_type = TAG_TYPE_BY_SECTION.get(
                            filt["section"], "text"
                        )
                        template_tags[tag_name] = _build_variable_tag(
                            tag_name, filt["name"], var_type
                        )
                        used_tag_names.append(tag_name)

                    viz = dict(chart.get("visualization_settings", {}))
                    if not viz:
                        viz = _visualization_defaults(
                            display,
                            chart.get("dimension"),
                            chart.get("metric"),
                            chart_sql,
                        )
                    log_info(
                        f"chart='{chart['title'][:40]}' "
                        f"viz={viz}"
                    )

                    crossfilter = chart.get("crossfilter")
                    if crossfilter:
                        source_tag = crossfilter.get("source_tag")
                        source_column = crossfilter.get("source_column")
                        param = filter_by_tag.get(source_tag)
                        if param and source_column:
                            viz["click_behavior"] = _build_crossfilter_behavior(
                                param["id"], source_column
                            )
                            if source_tag and source_tag in tag_to_filter_config:
                                if source_tag not in template_tags:
                                    filt_cfg = tag_to_filter_config[source_tag]
                                    var_type = TAG_TYPE_BY_SECTION.get(
                                        filt_cfg["section"], "text"
                                    )
                                    template_tags[source_tag] = _build_variable_tag(
                                        source_tag,
                                        filt_cfg["name"],
                                        var_type,
                                    )
                                if source_tag not in used_tag_names:
                                    used_tag_names.append(source_tag)

                    card_id = await _create_card(
                        client,
                        headers,
                        db_id,
                        chart["title"],
                        chart_sql,
                        display,
                        template_tags if template_tags else None,
                        viz if viz else None,
                    )
                    card_ids.append(card_id)

                    row, col, sx, sy = _resolve_layout(
                        chart.get("layout", (0, 0, 24, 8))
                    )

                    parameter_mappings: list[dict] = []
                    for tag_name in used_tag_names:
                        parameter_mappings.append({
                            "parameter_id": filter_by_tag[tag_name]["id"],
                            "card_id": card_id,
                            "target": ["variable", ["template-tag", tag_name]],
                        })

                    dashcard: dict[str, Any] = {
                        "id": dashcard_id,
                        "card_id": card_id,
                        "row": row,
                        "col": col,
                        "size_x": sx,
                        "size_y": sy,
                        "parameter_mappings": parameter_mappings,
                        "visualization_settings": {},
                    }
                    if pages:
                        dashcard["dashboard_tab_id"] = tab_id

                    dashcards_payload.append(dashcard)
                    dashcard_id -= 1

            payload: dict[str, Any] = {"dashcards": dashcards_payload}
            if pages:
                payload["tabs"] = tabs_payload
            if filter_payload:
                payload["parameters"] = filter_payload

            resp = await client.put(
                f"/api/dashboard/{dashboard_id}",
                headers=headers,
                json=payload,
            )

            if resp.status_code >= 400:
                conflict_id = _extract_conflict_id(resp.text)
                if conflict_id is not None:
                    log_warning(
                        f"dashboard: Metabase conflict on id={conflict_id}; "
                        f"removing and retrying"
                    )
                    try:
                        await client.delete(
                            f"/api/dashboard/{conflict_id}", headers=headers
                        )
                    except Exception as cleanup_exc:
                        log_error(
                            f"dashboard: cleanup failed: {cleanup_exc}"
                        )
                    resp = await client.put(
                        f"/api/dashboard/{dashboard_id}",
                        headers=headers,
                        json=payload,
                    )

            if resp.status_code >= 400:
                log_error(
                    f"Dashboard PUT failed: {resp.status_code} "
                    f"{resp.text[:400]}"
                )
            resp.raise_for_status()
            log_success(
                f"Dashboard {dashboard_id} built with "
                f"{len(work_pages)} pages, {len(card_ids)} cards, "
                f"{len(filter_payload)} filters"
            )

            embed_url = await _enable_public_link(
                client, headers, dashboard_id
            )

            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "card_ids": card_ids,
                "tabs": [p["name"] for p in work_pages] if pages else [],
                "filters": [f["name"] for f in filter_payload],
                "embed_url": embed_url,
                "error": None,
            }

    except httpx.HTTPStatusError as exc:
        log_error(
            f"Metabase HTTP {exc.response.status_code}: "
            f"{exc.response.text[:400]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard_dynamic failed: {exc}")
        return _fail(str(exc))


async def render_dashboard_interactive(
    title: str,
    pages: list[dict],
    filters: list[dict] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Multi-page dashboard with basic variable filters and cross-filtering.
    SQL convention: [[AND alias.column = {{tag}}]] for text variables.
    """
    log_process(
        f"render_dashboard_interactive: '{title}' "
        f"pages={len(pages)} filters={len(filters) if filters else 0}"
    )

    if not pages:
        return _fail("At least one page is required")

    try:
        async with httpx.AsyncClient(
            base_url=settings.METABASE_URL, timeout=300.0
        ) as client:
            token = await _authenticate()
            headers = {"X-Metabase-Session": token}

            db_id = await _get_supabase_database_id(client, headers)
            if not db_id:
                return _fail("No database found in Metabase")

            filter_payload: list[dict] = []
            filter_by_tag: dict[str, dict] = {}

            if filters:
                for filt in filters:
                    parameter: dict[str, Any] = {
                        "id": str(uuid.uuid4()),
                        "name": filt["name"],
                        "slug": filt["slug"],
                        "type": PARAM_TYPE_BY_SECTION.get(
                            filt["section"], "string/="
                        ),
                        "sectionId": filt["section"],
                    }
                    values = filt.get("values")
                    if values and isinstance(values, list):
                        parameter["values_source_type"] = "static-list"
                        parameter["values_source_config"] = {"values": values}
                    filter_payload.append(parameter)
                    filter_by_tag[filt["target_tag"]] = parameter

            dashboard_id = await _create_dashboard(
                client, headers, title, description
            )

            tabs_payload: list[dict] = []
            dashcards_payload: list[dict] = []
            card_ids: list[int] = []
            dashcard_id = -1

            for tab_idx, page in enumerate(pages):
                tab_id = -(tab_idx + 1)
                tabs_payload.append({"id": tab_id, "name": page["name"]})

                for chart in page["charts"]:
                    display = chart.get("display", "table")
                    if display not in VALID_DISPLAYS:
                        display = "table"

                    chart_sql = chart["sql"]
                    template_tags: dict = dict(chart.get("template_tags", {}))
                    used_tag_names: list[str] = []

                    if filters:
                        for filt in filters:
                            tag_name = filt["target_tag"]
                            marker = "{{" + tag_name + "}}"
                            if marker not in chart_sql:
                                continue
                            if tag_name in template_tags:
                                used_tag_names.append(tag_name)
                                continue

                            var_type = TAG_TYPE_BY_SECTION.get(
                                filt["section"], "text"
                            )
                            template_tags[tag_name] = _build_variable_tag(
                                tag_name, filt["name"], var_type
                            )
                            used_tag_names.append(tag_name)

                    viz = dict(chart.get("visualization_settings", {}))
                    if not viz:
                        viz = _visualization_defaults(
                            display,
                            chart.get("dimension"),
                            chart.get("metric"),
                            chart_sql,
                        )

                    crossfilter = chart.get("crossfilter")
                    if crossfilter and filters:
                        source_tag = crossfilter.get("source_tag")
                        source_column = crossfilter.get("source_column")
                        param = filter_by_tag.get(source_tag)
                        if param and source_column:
                            viz["click_behavior"] = _build_crossfilter_behavior(
                                param["id"], source_column
                            )
                            if source_tag not in used_tag_names:
                                used_tag_names.append(source_tag)
                            if source_tag not in template_tags:
                                filt_cfg = next(
                                    (
                                        f for f in filters
                                        if f["target_tag"] == source_tag
                                    ),
                                    None,
                                )
                                if filt_cfg:
                                    var_type = TAG_TYPE_BY_SECTION.get(
                                        filt_cfg["section"], "text"
                                    )
                                    template_tags[source_tag] = _build_variable_tag(
                                        source_tag,
                                        filt_cfg["name"],
                                        var_type,
                                    )

                    card_id = await _create_card(
                        client,
                        headers,
                        db_id,
                        chart["title"],
                        chart_sql,
                        display,
                        template_tags if template_tags else None,
                        viz if viz else None,
                    )
                    card_ids.append(card_id)

                    row, col, sx, sy = _resolve_layout(
                        chart.get("layout", "full")
                    )

                    parameter_mappings: list[dict] = []
                    for tag_name in used_tag_names:
                        parameter_mappings.append({
                            "parameter_id": filter_by_tag[tag_name]["id"],
                            "card_id": card_id,
                            "target": ["variable", ["template-tag", tag_name]],
                        })

                    dashcards_payload.append({
                        "id": dashcard_id,
                        "card_id": card_id,
                        "dashboard_tab_id": tab_id,
                        "row": row,
                        "col": col,
                        "size_x": sx,
                        "size_y": sy,
                        "parameter_mappings": parameter_mappings,
                        "visualization_settings": {},
                    })
                    dashcard_id -= 1

            payload: dict[str, Any] = {
                "tabs": tabs_payload,
                "dashcards": dashcards_payload,
            }
            if filter_payload:
                payload["parameters"] = filter_payload

            resp = await client.put(
                f"/api/dashboard/{dashboard_id}",
                headers=headers,
                json=payload,
            )
            if resp.status_code >= 400:
                conflict_id = _extract_conflict_id(resp.text)
                if conflict_id is not None:
                    log_warning(
                        f"dashboard: Metabase conflict on id={conflict_id}; "
                        f"removing and retrying"
                    )
                    try:
                        await client.delete(
                            f"/api/dashboard/{conflict_id}", headers=headers
                        )
                    except Exception as cleanup_exc:
                        log_error(
                            f"dashboard: cleanup failed: {cleanup_exc}"
                        )
                    resp = await client.put(
                        f"/api/dashboard/{dashboard_id}",
                        headers=headers,
                        json=payload,
                    )
            if resp.status_code >= 400:
                log_error(
                    f"Dashboard PUT failed: {resp.status_code} "
                    f"{resp.text[:400]}"
                )
            resp.raise_for_status()
            
            log_success(
                f"Dashboard {dashboard_id} built with "
                f"{len(tabs_payload)} tabs, {len(card_ids)} cards, "
                f"{len(filter_payload)} filters"
            )

            embed_url = await _enable_public_link(
                client, headers, dashboard_id
            )

            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "card_ids": card_ids,
                "tabs": [p["name"] for p in pages],
                "filters": [f["name"] for f in filters] if filters else [],
                "embed_url": embed_url,
                "error": None,
            }

    except httpx.HTTPStatusError as exc:
        log_error(
            f"Metabase HTTP {exc.response.status_code}: "
            f"{exc.response.text[:400]}"
        )
        return _fail(f"Metabase HTTP {exc.response.status_code}")
    except Exception as exc:
        log_error(f"render_dashboard_interactive failed: {exc}")
        return _fail(str(exc))