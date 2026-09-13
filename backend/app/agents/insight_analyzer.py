import json
from app.agents.llm import generate_chat
from app.core.logging import log_error

INSIGHT_SYSTEM_PROMPT = """You are a senior Business Intelligence Analyst.

Given a user question and query results (JSON sample), produce a concise business insight.

Rules:
- Respond in the same language as the user question (Indonesian or English).
- Highlight key numbers, trends, anomalies.
- Suggest 1-2 actionable next steps.
- Keep it under 150 words.
- No markdown, no code fences.
- If the result set is empty (0 rows), state clearly that no matching data was found. Do NOT invent information.
- IMPORTANT: If the total rows exceed the sample size, explicitly state that the analysis is based on a sample of N rows, not the entire dataset.
"""


def _truncate_results(results: list[dict], max_rows: int = 20) -> str:
    """Limit rows to avoid token bloat."""
    return json.dumps(results[:max_rows], default=str)


async def analyze(user_prompt: str, results: list[dict]) -> str:
    """Turn query results into a natural language business insight."""
    # Guard: no data -> do not hallucinate
    if not results:
        return (
            "Tidak ada data yang cocok dengan pertanyaan Anda di dataset. "
            "Coba periksa kembali kata kunci atau rentang tanggalnya."
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
        return "Gagal membuat insight dari hasil query."