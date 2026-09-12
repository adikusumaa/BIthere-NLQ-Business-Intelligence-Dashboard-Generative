from app.agents.llm import generate_chat
from app.services import metabase
from app.core.logging import log_info, log_error

DASHBOARD_SYSTEM_PROMPT = """You are a Dashboard Builder Agent.
Given a user request, return ONLY a JSON config:
{
  "dashboard_name": "...",
  "charts": [
    {"title": "...", "chart_type": "bar|line|pie|table", "x_axis": "...", "y_axis": "..."}
  ]
}
Return raw JSON only, no markdown.
"""


async def build_dashboard(user_prompt: str, query_results: list[dict]) -> dict:
    """Generate dashboard config, then create it in Metabase."""
    messages = [
        {"role": "system", "content": DASHBOARD_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await generate_chat(messages, temperature=0.0)
        import json
        config = json.loads(raw)

        dashboard = await metabase.create_dashboard(config["dashboard_name"])
        embed_url = metabase.get_embed_url(dashboard["id"])

        log_info(f"Dashboard created: {dashboard['id']}")
        return {"config": config, "dashboard_id": dashboard["id"], "embed_url": embed_url}
    except Exception as exc:
        log_error(f"Dashboard builder failed: {exc}")
        return {"config": None, "dashboard_id": None, "embed_url": None}