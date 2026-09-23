"""
SQL sanitizer: fix common LLM typos.
Patterns are carefully anchored so ORDER is not mangled into OR DER,
and AND/OR/ON are only fixed when followed by an alias with a dot.
"""

import re
from typing import Optional

from app.core.logging import logger


TYPO_PATTERNS = [
    # Missing space after keyword — only when followed immediately by word char
    (re.compile(r"\bSELECT(?=[A-Za-z_])", re.IGNORECASE), "SELECT "),
    (re.compile(r"\bFROM(?=[A-Za-z_])", re.IGNORECASE), "FROM "),
    (re.compile(r"\bWHERE(?=[A-Za-z_])", re.IGNORECASE), "WHERE "),
    (re.compile(r"\bJOIN(?=[A-Za-z_])", re.IGNORECASE), "JOIN "),
    (re.compile(r"\bGROUP\s+BY(?=[A-Za-z_])", re.IGNORECASE), "GROUP BY "),
    (re.compile(r"\bORDER\s+BY(?=[A-Za-z_])", re.IGNORECASE), "ORDER BY "),
    # AND/OR/ON — only if followed by "alias." pattern (word + dot)
    (re.compile(r"\bAND(?=[A-Za-z_]\w*\.)", re.IGNORECASE), "AND "),
    (re.compile(r"\bOR(?=[A-Za-z_]\w*\.)", re.IGNORECASE), "OR "),
    (re.compile(r"\bON(?=[A-Za-z_]\w*\.)", re.IGNORECASE), "ON "),
    # Fix already-mangled "OR DER BY" -> "ORDER BY"
    (re.compile(r"\bOR\s+DER\s+BY\b", re.IGNORECASE), "ORDER BY"),
    # Collapse multiple spaces
    (re.compile(r"[ \t]+"), " "),
]


def sanitize_sql(sql: Optional[str]) -> str:
    """
    Fix common SQL typos without changing semantics.
    Returns empty string if input is None/empty.
    """
    if not sql:
        return ""

    original = sql
    result = sql

    for pattern, replacement in TYPO_PATTERNS:
        result = pattern.sub(replacement, result)

    if result != original:
        logger.info("[PROCESS] SQL sanitizer applied fixes")

    return result