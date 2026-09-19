"""
Query Generator Agent.
Converts natural language questions into safe SQL queries.
Supports PostgreSQL, DuckDB, MySQL, SQLite dialects.
"""

import re

from app.agents.llm import generate_chat
from app.core.logging import log_info, log_error, log_warning


# Fallback schema used when no RAG context is available (v1 compat).
FINTECH_SCHEMA_HINT = """users:
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
"""


DIALECT_NOTES = {
    "postgresql": (
        "Type casts use :: syntax (amount::numeric). "
        "Use DATE 'YYYY-MM-DD' literals for dates."
    ),
    "duckdb": (
        "Type casts use :: syntax. Use DATE 'YYYY-MM-DD'. "
        "Supports QUALIFY and window functions."
    ),
    "mysql": (
        "Use backticks for identifiers when needed. "
        "Type casts use CAST(col AS type). "
        "Use DATE('YYYY-MM-DD') literals."
    ),
    "sqlite": (
        "SQLite is flexible with types. "
        "Use 'YYYY-MM-DD' string literals for dates. "
        "No native BOOLEAN; use 0/1."
    ),
}


QUERY_GEN_SYSTEM_PROMPT = """You are a SQL query generator for a Business Intelligence system.

{schema_section}

RULES:
- ONLY produce a single SELECT (or WITH...SELECT) statement.
- NEVER use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, CREATE.
- Use explicit JOINs with short aliases where sensible.
- Add LIMIT 1000 for non-aggregated queries if no LIMIT is present.
- Do NOT use placeholder syntax: no ":param", no "$1", no "?", no "{{ }}", no "%s".
- Write literal values directly. Example: WHERE status = 'active'.
- Do NOT include markdown, code fences, comments, or explanations.
- Return ONLY the SQL query.

DIALECT: {dialect}
{diag_notes}
"""


FORBIDDEN_PLACEHOLDER_PATTERNS = [
    (re.compile(r"(?<!:):[A-Za-z_]\w*"), ":param placeholder"),
    (re.compile(r"\$\d+"), "$n placeholder"),
    (re.compile(r"\{\{"), "{{ }} template tag"),
    (re.compile(r"%s"), "%s placeholder"),
]


def _extract_sql(raw: str) -> str:
    """Strip markdown code fences from LLM output if present."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _reject_placeholders(sql: str) -> None:
    """Raise if SQL contains any placeholder syntax."""
    for pattern, label in FORBIDDEN_PLACEHOLDER_PATTERNS:
        match = pattern.search(sql)
        if match:
            raise ValueError(
                f"Generated SQL contains forbidden {label}: {match.group(0)!r}"
            )


async def generate_query(
    user_prompt: str,
    metadata_context: str = "",
    api_key: str | None = None,
    dialect: str = "postgresql",
) -> str:
    """
    Generate a safe SQL query from natural language using RAG context.

    Args:
        user_prompt: User's natural-language question.
        metadata_context: Schema docs from RAG (empty = use FINTECH_SCHEMA_HINT).
        api_key: Workspace Groq key. If None, platform fallback.
        dialect: Target SQL dialect (postgresql | duckdb | mysql | sqlite).
    """
    if metadata_context and metadata_context.strip():
        schema_section = f"SCHEMA (from workspace RAG):\n{metadata_context}"
    else:
        schema_section = f"SCHEMA:\n{FINTECH_SCHEMA_HINT}"

    diag_notes = DIALECT_NOTES.get(dialect, DIALECT_NOTES["postgresql"])
    system_prompt = QUERY_GEN_SYSTEM_PROMPT.format(
        schema_section=schema_section,
        dialect=dialect,
        diag_notes=diag_notes,
    )

    user_message = (
        f"User question: {user_prompt}\n\n"
        f"SQL query:"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        raw = await generate_chat(messages, temperature=0.0, api_key=api_key)
    except Exception as exc:
        log_error(f"Query generator LLM call failed: {exc}")
        raise

    sql = _extract_sql(raw)
    log_info(f"Generated SQL length: {len(sql)} chars (dialect={dialect})")

    try:
        _reject_placeholders(sql)
    except ValueError as exc:
        log_warning(f"Placeholder detected: {exc}")
        log_warning(f"Problematic SQL: {sql[:300]}")
        raise

    return sql