import json
from app.agents.llm import generate_chat
from app.core.logging import log_info, log_error

PLANNER_SYSTEM_PROMPT = """You are a Planner Agent for a Business Intelligence system.

The system ONLY answers questions about a fintech fraud dataset with these tables:
- users (customer profiles)
- cards (card details)
- transactions (card transactions)
- fraud_labels (fraud labels)
- mcc_codes (merchant category codes)

If the user question is NOT about this dataset (e.g., general knowledge, other topics, chit-chat), set is_in_scope=false.

Analyze the user question and return ONLY a JSON object with this schema:
{
  "is_in_scope": true | false,
  "intent": "query_data" | "create_dashboard" | "send_report" | "combined",
  "entities": ["table1", "column2", ...],
  "filters": {"date_range": "...", "category": "..."},
  "needs_dashboard": true | false,
  "needs_report": true | false,
  "reasoning": "short explanation"
}
Do not include markdown, code fences, or extra text. Return raw JSON only.
"""


def _fallback(reason: str) -> dict:
    """Default plan when LLM fails or does not follow the schema."""
    return {
        "is_in_scope": False,
        "intent": "query_data",
        "entities": [],
        "filters": {},
        "needs_dashboard": False,
        "needs_report": False,
        "reasoning": reason,
    }


async def plan(user_prompt: str, session_state: dict | None = None) -> dict:
    """Analyze user intent and return structured plan."""
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await generate_chat(messages, temperature=0.0)
        plan_dict = json.loads(raw.strip())

        if not isinstance(plan_dict, dict):
            log_error(
                f"Planner returned non-dict JSON: {type(plan_dict).__name__}"
            )
            return _fallback("fallback due to non-object JSON")

        plan_dict.setdefault("is_in_scope", True)

        log_info(
            f"Planner result: intent={plan_dict.get('intent')}, "
            f"in_scope={plan_dict.get('is_in_scope')}"
        )
        return plan_dict

    except json.JSONDecodeError as exc:
        log_error(f"Planner returned invalid JSON: {exc}")
        return _fallback("fallback due to parse error")