"""
Auto-enrichment: track candidate terms from user prompts.
Terms exceeding a threshold can be promoted to the glossary.
"""

import re
from typing import List

from app.core.logging import logger
from app.services.cache import cache


TERM_THRESHOLD = 5
STOPWORDS = {
    "yang", "dan", "atau", "dengan", "untuk", "dari", "ke", "di",
    "the", "a", "an", "of", "for", "with", "from", "to",
    "berapa", "total", "bagaimana", "apa", "adalah",
    "monthly", "daily", "yearly", "top", "per",
}


def _candidate_terms(prompt: str) -> List[str]:
    """Extract candidate terms (words > 3 chars, not stopwords)."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_]{2,}\b", prompt.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 3]


def _counter_key(workspace_id: str, term: str) -> str:
    return f"ws:{workspace_id}:term:{term}"


async def track_terms(workspace_id: str, prompt: str) -> None:
    """Increment Redis counter for each candidate term in a prompt."""
    for term in set(_candidate_terms(prompt)):
        key = _counter_key(workspace_id, term)
        try:
            current = await cache.get(key) or 0
            await cache.set(key, int(current) + 1, ttl=7 * 24 * 3600)
        except Exception as exc:
            logger.warning(f"[WARNING] Term counter failed for '{term}': {exc}")


async def get_candidates(workspace_id: str, prompt_pool: List[str]) -> List[dict]:
    """
    Scan a pool of prompts, return terms that crossed TERM_THRESHOLD.
    Called periodically (e.g., via admin endpoint) to suggest new glossary entries.
    """
    counts: dict = {}
    for prompt in prompt_pool:
        for term in set(_candidate_terms(prompt)):
            counts[term] = counts.get(term, 0) + 1

    candidates = []
    for term, local_count in counts.items():
        key = _counter_key(workspace_id, term)
        try:
            stored = int(await cache.get(key) or 0)
        except Exception:
            stored = 0
        total = stored + local_count
        if total >= TERM_THRESHOLD:
            candidates.append({"term": term, "count": total})

    return sorted(candidates, key=lambda x: x["count"], reverse=True)