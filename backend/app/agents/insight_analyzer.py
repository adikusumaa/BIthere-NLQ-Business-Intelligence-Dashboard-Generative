import json
from app.agents.llm import generate_chat
from app.core.logging import log_error


INSIGHT_SYSTEM_PROMPT = """You are a senior Business Intelligence Analyst.
Given a user question and query results (JSON), produce a concise business insight.

Rules:
- Respond in the same language as the user question (Indonesian or English).
- Highlight key numbers, trends, anomalies.
- Suggest 1-2 actionable next steps.
- Keep it under 150 words.
- No markdown, no code fences.
"""

FALLBACK_MESSAGE = "Sorry, failed to generate an insight from the query results."


def _truncate_results(results: list[dict], max_rows: int = 20) -> str:
    """Limit rows to avoid token bloat."""
    return json.dumps(results[:max_rows], default=str)


async def analyze(user_prompt: str, results: list[dict]) -> str:
    """Turn query results into a natural language business insight."""
    user_message = (
        f"User question: {user_prompt}\n\n"
        f"Query results ({len(results)} rows, showing up to 20):\n"
        f"{_truncate_results(results)}"
    )

    messages = [
        {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        return await generate_chat(messages, temperature=0.3)
    except Exception as exc:
        log_error(f"Insight analyzer failed: {exc}")
        return FALLBACK_MESSAGE