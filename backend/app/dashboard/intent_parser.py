"""
Intent Parser Agent (F-13).
Translates a natural-language instruction into a structured Patch, using the
workspace's Groq key and a summary of the current dashboard state.
Injects the workspace schema hint so the LLM does not hallucinate
table/column names.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

from app.agents.llm import generate_chat
from app.core.logging import logger
from app.dashboard.patch_model import parse_patch
from app.dashboard.state_model import DashboardState
from app.dashboard.state_summarizer import summarize_state
from app.services.cache import cache


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "intent_parser.md"
PATCH_CACHE_TTL = 3600


class IntentParseError(Exception):
    """Raised when the LLM output cannot be parsed into a valid patch."""


def _load_prompt_template() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise IntentParseError(f"Prompt template not found: {PROMPT_PATH}")


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _cache_key(instruction: str, state: DashboardState) -> str:
    payload = f"{instruction.strip().lower()}|v{state.version}"
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"patch:{h}"


async def parse_instruction(
    instruction: str,
    state: DashboardState,
    api_key: Optional[str] = None,
    redis_prefix: str = "",
    schema_hint: str = "",
) -> Any:
    """
    Translate a natural-language instruction into a validated Patch object.

    Args:
        instruction: User's editing instruction.
        state: Current DashboardState (version, pages, cards).
        api_key: Workspace Groq key. If None, platform key is used.
        redis_prefix: Workspace redis prefix for cached patch reuse.
        schema_hint: Optional schema string ("table(col1, col2, ...)" per line).

    Returns:
        A Patch instance (AddCardPatch, RemoveCardPatch, ..., or CompositePatch).

    Raises:
        IntentParseError if LLM output is unusable even after retry.
    """
    if not instruction or not instruction.strip():
        raise IntentParseError("Empty instruction")

    key = _cache_key(instruction, state)
    cached = await cache.get(key)
    if cached:
        logger.info(f"[PROCESS] Intent parser cache hit: {key}")
        try:
            return parse_patch(cached)
        except Exception:
            logger.warning("[WARNING] Cached patch invalid, regenerating")

    template = _load_prompt_template()

    if schema_hint and schema_hint.strip():
        schema_context = schema_hint.strip()
    else:
        schema_context = "(no schema available; prefer non-ADD_CARD patches)"

    prompt = (
        template
        .replace("{state_summary}", summarize_state(state))
        .replace("{instruction}", instruction.strip())
        .replace("{schema_context}", schema_context)
    )

    messages = [
        {"role": "system", "content": "You are a dashboard patch generator. Output raw JSON only."},
        {"role": "user", "content": prompt},
    ]

    raw = await generate_chat(messages, temperature=0.0, api_key=api_key)
    cleaned = _strip_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("[WARNING] Intent parser: invalid JSON, retrying with reminder")
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    "Your previous answer was not valid JSON. "
                    "Return ONLY the raw JSON patch now, without any "
                    "explanation or markdown."
                ),
            },
        ]
        raw2 = await generate_chat(retry_messages, temperature=0.0, api_key=api_key)
        cleaned2 = _strip_fences(raw2)
        try:
            data = json.loads(cleaned2)
        except json.JSONDecodeError as exc:
            raise IntentParseError(f"LLM did not return valid JSON: {exc}") from exc

    try:
        patch = parse_patch(data)
    except Exception as exc:
        raise IntentParseError(f"Invalid patch structure: {exc}") from exc

    try:
        await cache.set(key, data, ttl=PATCH_CACHE_TTL)
    except Exception:
        pass

    logger.info(f"[SUCCESS] Intent parsed: {data.get('patch_type')}")
    return patch