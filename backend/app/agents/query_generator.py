import re
from app.agents.llm import generate_chat
from app.core.logging import log_info

QUERY_GEN_SYSTEM_PROMPT = """You are a SQL Query Generator for PostgreSQL.
Given the user's question and the database schema context, produce ONE valid SELECT query.

Dataset schema facts (MUST follow):
- `fraud_labels.fraud_label` is TEXT with values 'Yes' or 'No'.
  NEVER compare fraud_label to TRUE / FALSE / 1 / 0.
  Always use: fraud_label = 'Yes' or fraud_label = 'No'.
- `transactions.date` is TIMESTAMP. Filter dates with explicit ranges, e.g.:
  date >= DATE '2010-01-01' AND date < DATE '2010-02-01'.
- `transactions.errors` is TEXT and may be NULL. Empty error means errors IS NULL or errors = ''.
- `cards.card_on_dark_web` is BOOLEAN (true / false).

Join keys:
- transactions.client_id = users.id
- transactions.card_id   = cards.id
- transactions.mcc       = mcc_codes.mcc_code
- transactions.id        = fraud_labels.id

Rules:
- ONLY SELECT statements.
- NEVER use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER.
- Use explicit JOINs when needed.
- Always add LIMIT 1000 for exploratory queries if no aggregation.
- Return ONLY the SQL query, no markdown, no explanation.
"""


def _extract_sql(raw: str) -> str:
    """Strip code fences if LLM wraps SQL in them."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


async def generate_query(user_prompt: str, metadata_context: str) -> str:
    """Generate SQL query from natural language using RAG context."""
    user_message = (
        f"Schema context:\n{metadata_context}\n\n"
        f"User question: {user_prompt}\n\n"
        f"SQL query:"
    )

    messages = [
        {"role": "system", "content": QUERY_GEN_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    raw = await generate_chat(messages, temperature=0.0)
    sql = _extract_sql(raw)
    log_info(f"Generated SQL length: {len(sql)} chars")
    return sql