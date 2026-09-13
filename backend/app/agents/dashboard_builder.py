"""
Dashboard Builder Agent (PRJ 4.7).

Converts a natural-language request into a full dashboard configuration
and renders it in Metabase via the MCP render_dashboard tool.
"""

import json
import re

from app.agents.llm import generate_chat
from app.core.logging import log_process, log_info, log_error


SCHEMA_CONTEXT = """
Available tables and columns (PostgreSQL database: Supabase):

users:
  id, current_age, retirement_age, birth_year, birth_month,
  gender (Male | Female), address, latitude, longitude,
  per_capita_income, yearly_income, total_debt,
  credit_score, num_credit_cards

cards:
  id, client_id, card_brand (Visa | Mastercard | Discover | Amex),
  card_type (Credit | Debit | Debit (Prepaid)), credit_limit,
  acct_open_date, card_on_dark_web

transactions:
  id, date (timestamp), client_id, card_id, amount, use_chip,
  merchant_id, merchant_city, merchant_state, mcc, errors

fraud_labels:
  id, fraud_label (Yes | No)

mcc_codes:
  mcc_code, description
"""


DASHBOARD_SYSTEM_PROMPT = f"""You are a Dashboard Builder Agent for a fintech fraud analytics platform.

Produce a complete dashboard configuration as a SINGLE JSON object.
Output raw JSON only. No markdown, no prose, no code fences.

{SCHEMA_CONTEXT}

Output JSON schema:
{{
  "title": "string",
  "description": "string",
  "filters": [
    {{
      "name": "string",
      "slug": "string",
      "section": "category" | "number" | "date",
      "target_tag": "string",
      "values": ["allowed_value_1", "allowed_value_2"]
    }}
  ],
  "pages": [
    {{
      "name": "string",
      "charts": [
        {{
          "title": "string",
          "sql": "string",
          "display": "scalar|gauge|bar|row|line|area|combo|pie|donut|table|funnel|progress|scatter|waterfall",
          "layout": [row, col, size_x, size_y],
          "dimension": "column_name_or_alias",
          "metric": "column_alias",
          "visualization_settings": {{}},
          "crossfilter": {{ "source_tag": "string", "source_column": "string" }}
        }}
      ]
    }}
  ]
}}

Page rules:
- If the user mentions "multi-page", "tabs", "pages", or separate sections,
  use "pages" with two or more entries.
- Otherwise, still use "pages" with a single entry named "Main".

Chart rules:
- Every chart MUST include "dimension" and "metric", except:
    - scalar / smartscalar: only "metric"
    - gauge: only "metric"
    - table: both may be null
- For pie / donut / funnel / progress / waterfall:
    "dimension" is the category column alias,
    "metric" is the numeric column alias.
- "metric" must exactly match the SQL alias.
- "dimension" must exactly match the SQL column name or alias.

Filter values rules:
- Each filter must include a "values" array listing up to 20 distinct values.
- Card Brand: ["Visa", "Mastercard", "Discover", "Amex"]
- Card Type: ["Credit", "Debit", "Debit (Prepaid)"]
- Chip Usage: ["Chip Transaction", "Swipe Transaction", "Online Transaction"]
- Gender: ["Male", "Female"]
- State or city filters: use an empty array [].

SQL rules:
- Only SELECT statements.
- Table aliases: t (transactions), c (cards), u (users), f (fraud_labels), m (mcc_codes).
- Join keys: t.client_id = u.id, t.card_id = c.id, t.mcc = m.mcc_code, t.id = f.id.
- Fraud filter: f.fraud_label = 'Yes'.
- Optional filters: [[AND alias.column = {{{{tag_name}}}}]].
- Never add quotes around {{{{tag_name}}}}.
- Non-aggregated queries must include LIMIT.

Layout grid is 24 columns wide:
- KPI row:    [0, 0, 6, 4], [0, 6, 6, 4], [0, 12, 6, 4], [0, 18, 6, 4]
- Half width: [row, 0, 12, 8] or [row, 12, 12, 8]
- Full width: [row, 0, 24, 8]
- Increment row by 8 between rows.

Filter and cross-filter rules:
- One filter per text column used in a WHERE clause.
- filter.target_tag must exactly match the tag used in SQL.
- The chart that drives a filter must NOT reference that filter tag in its SQL.
- Add crossfilter only to charts whose dimension matches a filter column.
"""


RETRY_PROMPT_SUFFIX = """

CRITICAL REMINDER:
Return ONLY the JSON object. Do not write any text before or after.
Do not wrap the JSON in markdown code fences.
Start your response with the character { and end with }.
"""


def _extract_json_object(raw: str) -> str | None:
    """Extract a JSON object from raw LLM output."""
    if not raw:
        return None

    text = raw.strip()

    fence_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        return fence_match.group(1).strip()

    if text.startswith("{"):
        depth = 0
        in_string = False
        escape = False
        for idx, ch in enumerate(text):
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[: idx + 1]

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    return None


def _validate_config(config: dict) -> tuple[bool, str]:
    """Check required fields and shape."""
    if not isinstance(config, dict):
        return False, "not a dict"
    if not config.get("title"):
        return False, "missing title"

    pages = config.get("pages")
    charts = config.get("charts")

    if pages:
        if not isinstance(pages, list) or not pages:
            return False, "pages must be a non-empty list"
        chart_lists = [p.get("charts", []) for p in pages]
    elif charts:
        chart_lists = [charts]
    else:
        return False, "missing both charts and pages"

    for chart_list in chart_lists:
        if not isinstance(chart_list, list):
            return False, "charts must be a list"
        for idx, chart in enumerate(chart_list):
            if not chart.get("title"):
                return False, f"chart {idx}: missing title"
            if not chart.get("sql"):
                return False, f"chart {idx}: missing sql"
            if not chart.get("display"):
                return False, f"chart {idx}: missing display"
            layout = chart.get("layout")
            if not (isinstance(layout, (list, tuple)) and len(layout) == 4):
                return False, f"chart {idx}: bad layout"

    filters = config.get("filters", [])
    if not isinstance(filters, list):
        return False, "filters not a list"
    for idx, filt in enumerate(filters):
        if not filt.get("name") or not filt.get("slug") or not filt.get("target_tag"):
            return False, f"filter {idx}: missing fields"

    return True, ""


async def _llm_call(messages: list[dict]) -> str | None:
    """Call the LLM and return the raw text, or None on failure."""
    try:
        return await generate_chat(messages, temperature=0.0, max_tokens=8192)
    except Exception as exc:
        log_error(f"dashboard_builder: LLM call failed: {exc}")
        return None


def _try_parse(raw: str) -> dict | None:
    """Extract, parse and validate JSON from raw LLM output."""
    extracted = _extract_json_object(raw)
    if not extracted:
        return None
    try:
        config = json.loads(extracted)
    except json.JSONDecodeError as exc:
        log_error(f"dashboard_builder: JSON decode failed: {exc}")
        return None
    if not isinstance(config, dict):
        return None
    valid, reason = _validate_config(config)
    if not valid:
        log_error(f"dashboard_builder: config invalid: {reason}")
        return None
    return config


async def generate_dashboard_config(user_prompt: str) -> dict | None:
    """
    Ask the LLM for a full dashboard configuration.

    Attempts once. If the response cannot be parsed, retries with an
    explicit reminder to output raw JSON.
    """
    log_process("dashboard_builder: generating config via LLM")

    messages = [
        {"role": "system", "content": DASHBOARD_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw = await _llm_call(messages)
    if raw:
        log_info(f"dashboard_builder: LLM raw output length={len(raw)}")
        config = _try_parse(raw)
        if config:
            n_pages = len(config.get("pages", []))
            n_charts = sum(len(p.get("charts", [])) for p in config.get("pages", []))
            if not n_pages and config.get("charts"):
                n_charts = len(config.get("charts", []))
            log_info(
                f"dashboard_builder: config ok "
                f"title='{config.get('title', '')[:40]}' "
                f"pages={n_pages} charts={n_charts} "
                f"filters={len(config.get('filters', []))}"
            )
            return config
        log_error("dashboard_builder: first attempt parse failed")
        log_error(f"dashboard_builder: raw preview: {raw[:500]}")

    log_process("dashboard_builder: retrying with reminder prompt")

    retry_messages = [
        {"role": "system", "content": DASHBOARD_SYSTEM_PROMPT + RETRY_PROMPT_SUFFIX},
        {"role": "user", "content": user_prompt},
    ]

    raw_retry = await _llm_call(retry_messages)
    if not raw_retry:
        log_error("dashboard_builder: retry returned nothing")
        return None

    log_info(f"dashboard_builder: retry output length={len(raw_retry)}")
    config = _try_parse(raw_retry)
    if not config:
        log_error("dashboard_builder: retry parse failed")
        log_error(f"dashboard_builder: retry preview: {raw_retry[:500]}")
        return None

    log_info("dashboard_builder: retry config ok")
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