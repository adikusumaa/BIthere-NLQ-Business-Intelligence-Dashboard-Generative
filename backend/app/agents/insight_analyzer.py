import json
from app.agents.llm import generate_chat
from app.core.logging import log_error

INSIGHT_SYSTEM_PROMPT = """You are a senior Business Intelligence analyst.

Given a user question and query results, produce a CONCISE executive insight.
ALWAYS respond in English, regardless of the language of the user question.

Structure (use markdown, keep it tight):
1. One executive summary paragraph (max 2 sentences, ~30 words).
2. Section "**Key Findings**" with 3 to 5 bullets. Each bullet starts with "- " and is max 15 words.
3. Section "**Recommended Actions**" with 1 to 3 numbered items. Each item is max 15 words.

Total length must be under 130 words. No fluff, no preamble, no closing remark.
Do NOT write "Best regards" or any signature. Do NOT repeat the question.
If the result set is empty, state that no matching data was found.
"""


def _truncate_results(results: list[dict], max_rows: int = 20) -> str:
    """Limit rows to avoid token bloat."""
    return json.dumps(results[:max_rows], default=str)


async def analyze(user_prompt: str, results: list[dict]) -> str:
    """Turn query results into a natural language business insight."""
    # Guard: no data -> do not hallucinate
    if not results:
        return (
            "**Summary**\n"
            "No matching data was found for this query.\n\n"
            "**Recommended Actions**\n"
            "1. Refine the date range or filters and try again."
        )

    total_rows = len(results)
    sample_rows = results[:20]
    sample_size = len(sample_rows)

    if total_rows > sample_size:
        header = (
            f"User question: {user_prompt}\n\n"
            f"Total rows returned: {total_rows}\n"
            f"Showing first {sample_size} rows as SAMPLE (not the whole dataset):\n"
        )
    else:
        header = (
            f"User question: {user_prompt}\n\n"
            f"Total rows returned: {total_rows} (all shown):\n"
        )

    user_message = header + _truncate_results(results)

    messages = [
        {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        return await generate_chat(messages, temperature=0.3)
    except Exception as exc:
        log_error(f"Insight analyzer failed: {exc}")
        return (
            "**Summary**\n"
            "Insight generation failed.\n\n"
            "**Recommended Actions**\n"
            "1. Retry the request."
        )