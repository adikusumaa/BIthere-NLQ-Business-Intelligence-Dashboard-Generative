"""
Query Generator Agent.
Converts natural language questions into safe SQL queries (PostgreSQL dialect).
"""

import re

from app.agents.llm import generate_chat
from app.core.logging import log_info, log_error


QUERY_GEN_SYSTEM_PROMPT = """You are a PostgreSQL query generator for a fintech fraud-detection dataset.

SCHEMA (only these columns exist, never invent new ones):

users:
  id, current_age, retirement_age, birth_year, birth_month,
  gender, address, latitude, longitude, per_capita_income,
  yearly_income, total_debt, credit_score, num_credit_cards

cards:
  id, client_id, card_brand, card_type, card_number, expires, cvv,
  has_chip, num_cards_issued, credit_limit, acct_open_date,
  year_pin_last_changed, card_on_dark_web

transactions:
  id, date, client_id, card_id, amount, use_chip,
  merchant_id, merchant_city, merchant_state, zip, mcc, errors

fraud_labels:
  id, fraud_label (values: 'Yes' or 'No')

mcc_codes:
  mcc_code, description

JOIN KEYS:
- transactions.client_id = users.id
- transactions.card_id = cards.id
- transactions.mcc = mcc_codes.mcc_code
- transactions.id = fraud_labels.id

RULES:
- ONLY produce a single SELECT statement.
- NEVER use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, CREATE.
- Use explicit JOINs with aliases: t, c, u, f, m.
- Fraud filter: f.fraud_label = 'Yes' (TEXT, use quotes).
- Date filter: use explicit ranges like
    date >= DATE '2010-01-01' AND date < DATE '2010-02-01'.
- Geographic: use t.merchant_state or t.merchant_city (NOT u.state).
- Add LIMIT 1000 for non-aggregated queries if no LIMIT is present.
- Return ONLY the SQL query, no markdown, no explanation, no code fences.
"""


def _extract_sql(raw: str) -> str:
    """Strip markdown code fences from LLM output if present."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


async def generate_query(user_prompt: str, metadata_context: str) -> str:
    """Generate a safe SQL query from natural language using RAG context."""
    user_message = (
        f"Additional schema context from RAG:\n{metadata_context}\n\n"
        f"User question: {user_prompt}\n\n"
        f"SQL query:"
    )

    messages = [
        {"role": "system", "content": QUERY_GEN_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await generate_chat(messages, temperature=0.0)
    except Exception as exc:
        log_error(f"Query generator LLM call failed: {exc}")
        raise

    sql = _extract_sql(raw)
    log_info(f"Generated SQL length: {len(sql)} chars")
    return sql