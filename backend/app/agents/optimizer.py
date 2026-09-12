import re
from app.core.logging import log_info, log_warning

INDEXED_COLUMNS = {
    "transactions": ["card_id", "date", "mcc", "client_id"],
    "cards": ["client_id"],
    "fraud_labels": ["fraud_label"],
}

DEFAULT_LIMIT = 1000


def _has_limit(sql: str) -> bool:
    return bool(re.search(r"\bLIMIT\b", sql, re.IGNORECASE))


def _has_aggregation(sql: str) -> bool:
    return bool(re.search(r"\b(COUNT|SUM|AVG|MIN|MAX|GROUP BY)\b", sql, re.IGNORECASE))


def optimize_query(sql: str) -> str:
    """Apply simple heuristics to make query efficient."""
    optimized = sql.strip().rstrip(";")

    if not _has_aggregation(optimized) and not _has_limit(optimized):
        optimized = f"{optimized} LIMIT {DEFAULT_LIMIT}"
        log_info(f"Added LIMIT {DEFAULT_LIMIT}")

    if "SELECT *" in optimized.upper():
        log_warning("Query uses SELECT * — consider explicit columns")

    return optimized