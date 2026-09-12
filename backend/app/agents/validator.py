import re
from app.core.logging import log_warning


FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT",
    "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC",
    "ATTACH", "DETACH", "MERGE", "CALL",
]

MAX_QUERY_LENGTH = 10_000


class QueryValidationError(Exception):
    """Raised when a generated SQL query fails safety checks."""


def validate_query(sql: str) -> str:
    """Validate SQL is safe. Returns the query if OK, raises otherwise."""
    # 1. Empty check
    if not sql or not sql.strip():
        raise QueryValidationError("Empty query")

    # 2. Length limit
    if len(sql) > MAX_QUERY_LENGTH:
        raise QueryValidationError(f"Query exceeds {MAX_QUERY_LENGTH} chars")

    normalized = sql.strip().upper()

    # 3. Forbidden keywords FIRST (more specific error message)
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, normalized):
            log_warning(f"Blocked keyword detected: {keyword}")
            raise QueryValidationError(f"Forbidden keyword: {keyword}")

    # 4. Must start with SELECT or WITH
    if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
        raise QueryValidationError("Only SELECT or WITH queries are allowed")

    # 5. Multi-statement check
    if ";" in sql.rstrip(";"):
        raise QueryValidationError("Multiple statements are not allowed")

    return sql