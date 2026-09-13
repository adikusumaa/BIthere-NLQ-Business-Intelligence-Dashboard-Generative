"""
Dashboard Builder Agent (PRJ 4.7).

Converts a natural-language request into a full dashboard configuration
and renders it in Metabase via the MCP render_dashboard tool.
"""

import json

from app.agents.llm import generate_chat
from app.core.logging import log_process, log_info, log_error


SCHEMA_CONTEXT = """
Available tables and columns (PostgreSQL database: Supabase):

users (1,219 rows):
  id (integer, primary key)
  current_age (integer)
  retirement_age (integer)
  birth_year (integer)
  birth_month (integer)
  gender (text: 'Male' | 'Female')
  address (text)
  latitude (float)
  longitude (float)
  per_capita_income (float)
  yearly_income (float)
  total_debt (float)
  credit_score (integer)
  num_credit_cards (integer)

cards (4,061 rows):
  id (integer, primary key)
  client_id (integer, foreign key to users.id)
  card_brand (text: 'Visa' | 'Mastercard' | 'Discover' | 'Amex')
  card_type (text: 'Credit' | 'Debit' | 'Debit (Prepaid)')
  credit_limit (float)
  acct_open_date (date)
  card_on_dark_web (boolean)

transactions (1,000,000 rows):
  id (integer, primary key)
  date (timestamp)
  client_id (integer, foreign key to users.id)
  card_id (integer, foreign key to cards.id)
  amount (numeric)
  use_chip (text: 'Swipe Transaction' | 'Online Transaction' | 'Chip Transaction')
  merchant_id (integer)
  merchant_city (text)
  merchant_state (text)
  mcc (integer, foreign key to mcc_codes.mcc_code)
  errors (text)

fraud_labels (1,000,000 rows):
  id (integer, primary key, matches transactions.id)
  fraud_label (text: 'Yes' | 'No')

mcc_codes (109 rows):
  mcc_code (integer, primary key)
  description (text)
"""


DASHBOARD_SYSTEM_PROMPT = f"""You are a Dashboard Builder Agent for a fintech fraud analytics platform.

Given a user's natural-language request, produce a complete dashboard
configuration as a single JSON object. The configuration is consumed
directly by the renderer. Output raw JSON only. No markdown.

{SCHEMA_CONTEXT}

Output JSON schema:
{{
  "title": "<dashboard title>",
  "description": "<one-sentence description>",
  "filters": [
    {{
      "name": "<display name>",
      "slug": "<url slug, lowercase>",
      "section": "category" | "string" | "location/state" | "location/city" | "number" | "date",
      "target_tag": "<sql_var_name>"
    }}
  ],
  "charts": [
    {{
      "title": "<chart title>",
      "sql": "<PostgreSQL SELECT query>",
      "display": "scalar" | "smartscalar" | "gauge" | "bar" | "bar/stacked" | "row" | "line" | "area" | "combo" | "pie" | "donut" | "table" | "funnel" | "progress" | "scatter" | "waterfall",
      "layout": [row, col, size_x, size_y],
      "dimension": "<column name for chart category or x-axis>",
      "metric": "<column alias for chart value or y-axis>",
      "visualization_settings": {{}},
      "crossfilter": {{ "source_tag": "<target_tag>", "source_column": "<column alias>" }}
    }}
  ]
}}

SQL rules:
- Only SELECT statements.
- Use explicit JOINs with these aliases: t (transactions), c (cards), u (users), f (fraud_labels), m (mcc_codes).
- Never hardcode a filter value.
- For optional filters use [[AND alias.column = {{{{tag_name}}}}]].
  The renderer drops the [[ ]] block when the filter is empty.
- For text variables Metabase adds quotes automatically; do not add quotes.
- Standard join keys: t.client_id = u.id, t.card_id = c.id, t.mcc = m.mcc_code, t.id = f.id.
- Fraud filter: f.fraud_label = 'Yes'.
- For non-aggregated queries add LIMIT.

Layout rules (grid is 24 columns wide):
- KPI row:  [0, 0, 6, 4], [0, 6, 6, 4], [0, 12, 6, 4], [0, 18, 6, 4]
- Half width: [row, 0, 12, 8] or [row, 12, 12, 8]
- Full width: [row, 0, 24, 8]
- Increment row by 8 after each full or half-width row; KPI row uses size_y=4.

Filter and cross-filter rules:
- Propose one filter per text column that appears in WHERE clauses.
- The filter "target_tag" must exactly match the tag used in SQL.
- Add "crossfilter" only to charts whose dimension matches a filter column.
- Do not reference {{brand_filter}} inside the SQL of the chart that drives brand_filter
  (it must keep showing every brand so the user can pick a different one).
- Same rule applies to state_filter and city_filter.
"""


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences if the LLM wrapped the JSON."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("\n", 1)
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def _validate_config(config: dict) -> tuple[bool, str]:
    """Check that required fields are present and well formed."""
    if not isinstance(config, dict):
        return False, "config is not a dict"
    if not config.get("title"):
        return False, "missing title"
    charts = config.get("charts")
    if not isinstance(charts, list) or not charts:
        return False, "missing or empty charts"

    for idx, chart in enumerate(charts):
        if not chart.get("title"):
            return False, f"chart {idx} missing title"
        if not chart.get("sql"):
            return False, f"chart {idx} missing sql"
        if not chart.get("display"):
            return False, f"chart {idx} missing display"
        layout = chart.get("layout")
        if not (isinstance(layout, (list, tuple)) and len(layout) == 4):
            return False, f"chart {idx} layout must be [row, col, size_x, size_y]"

    filters = config.get("filters", [])
    if not isinstance(filters, list):
        return False, "filters must be a list"

    for idx, filt in enumerate(filters):
        if not filt.get("name") or not filt.get("slug") or not filt.get("target_tag"):
            return False, f"filter {idx} missing required fields"

    return True, ""


async def generate_dashboard_config(user_prompt: str) -> dict | None:
    """
    Ask the LLM for a full dashboard configuration.

    Returns the config dict on success, or None on failure.
    """
    log_process("dashboard_builder: generating config via LLM")

    messages = [
        {"role": "system", "content": DASHBOARD_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await generate_chat(messages, temperature=0.1)
    except Exception as exc:
        log_error(f"dashboard_builder: LLM call failed: {exc}")
        return None

    cleaned = _strip_code_fences(raw)

    try:
        config = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        log_error(f"dashboard_builder: JSON decode failed: {exc}")
        return None

    valid, reason = _validate_config(config)
    if not valid:
        log_error(f"dashboard_builder: config validation failed: {reason}")
        return None

    log_info(
        f"dashboard_builder: config generated "
        f"title='{config.get('title', '')[:40]}' "
        f"charts={len(config.get('charts', []))} "
        f"filters={len(config.get('filters', []))}"
    )
    return config


async def build_dashboard(
    user_prompt: str,
    query_results: list[dict] | None = None,
) -> dict:
    """
    Build a Metabase dashboard from a natural-language request.

    Args:
        user_prompt: The original NLQ prompt from the user.
        query_results: Reserved for future use.

    Returns:
        dict with keys: success, config, dashboard_id, embed_url, error.
    """
    log_process(f"dashboard_builder: '{user_prompt[:60]}'")

    config = await generate_dashboard_config(user_prompt)
    if not config:
        return {
            "success": False,
            "config": None,
            "dashboard_id": None,
            "embed_url": None,
            "error": "Failed to generate dashboard configuration",
        }

    from app.mcp.tools.render_dashboard import render_dashboard_dynamic

    result = await render_dashboard_dynamic(config)

    if result.get("success"):
        log_info(f"dashboard_builder: rendered id={result.get('dashboard_id')}")
    else:
        log_error(f"dashboard_builder: render failed: {result.get('error')}")

    return {
        "success": bool(result.get("success")),
        "config": config,
        "dashboard_id": result.get("dashboard_id"),
        "embed_url": result.get("embed_url"),
        "error": result.get("error"),
    }