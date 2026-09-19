"""
Patch validator: checks patches against the current state before apply.
"""

import re
from typing import Any, List, Optional

from pydantic import BaseModel

from app.dashboard.grid import is_valid_position
from app.dashboard.patch_model import (
    AddCardPatch,
    AddFilterPatch,
    ChangeChartTypePatch,
    ChangeColorPatch,
    ChangeTitlePatch,
    CompositePatch,
    MoveCardPatch,
    RemoveCardPatch,
    RemoveFilterPatch,
    ResizeCardPatch,
    RollbackToVersionPatch,
    SwapCardsPatch,
    UpdateSqlPatch,
)
from app.dashboard.state_model import (
    DashboardState,
    all_card_ids,
    find_card,
    find_filter,
    find_page,
)


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
VALID_CHART_TYPES = {"scalar", "bar", "line", "pie", "area", "table", "text"}
FORBIDDEN_SQL_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT",
    "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC",
    "ATTACH", "DETACH", "MERGE", "CALL",
]


class ValidationResult(BaseModel):
    valid: bool
    reason: Optional[str] = None


def _ok() -> ValidationResult:
    return ValidationResult(valid=True)


def _fail(reason: str) -> ValidationResult:
    return ValidationResult(valid=False, reason=reason)


def _is_safe_sql(sql: str) -> Optional[str]:
    """Return None if safe, else the reason it is unsafe."""
    if not sql or not sql.strip():
        return "SQL is empty"
    normalized = sql.strip().upper()
    for kw in FORBIDDEN_SQL_KEYWORDS:
        if re.search(rf"\b{kw}\b", normalized):
            return f"Forbidden keyword: {kw}"
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return "Only SELECT or WITH queries are allowed"
    if ";" in sql.rstrip(";"):
        return "Multiple statements are not allowed"
    return None


def _validate_single(patch: Any, state: DashboardState, new_titles: set) -> ValidationResult:
    """Validate one non-composite patch. Mutates new_titles to track uniqueness."""
    if isinstance(patch, AddCardPatch):
        page = find_page(state, patch.page_id)
        if not page:
            return _fail(f"page_id '{patch.page_id}' not found")
        if patch.insert_before and find_card(state, patch.insert_before) is None:
            return _fail(f"insert_before card '{patch.insert_before}' not found")
        if patch.insert_after and find_card(state, patch.insert_after) is None:
            return _fail(f"insert_after card '{patch.insert_after}' not found")
        if patch.card.id in all_card_ids(state):
            return _fail(f"card id '{patch.card.id}' already exists")
        if not is_valid_position(patch.card.position):
            return _fail("card position out of bounds")
        if patch.card.type not in VALID_CHART_TYPES:
            return _fail(f"invalid card type '{patch.card.type}'")
        if patch.card.title in new_titles:
            return _fail(f"card title '{patch.card.title}' already used")
        new_titles.add(patch.card.title)
        if patch.card.sql:
            err = _is_safe_sql(patch.card.sql)
            if err:
                return _fail(err)
        return _ok()

    if isinstance(patch, RemoveCardPatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        return _ok()

    if isinstance(patch, MoveCardPatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        if not is_valid_position(patch.new_position):
            return _fail("new_position out of bounds")
        return _ok()

    if isinstance(patch, SwapCardsPatch):
        if find_card(state, patch.card_id_a) is None:
            return _fail(f"card '{patch.card_id_a}' not found")
        if find_card(state, patch.card_id_b) is None:
            return _fail(f"card '{patch.card_id_b}' not found")
        if patch.card_id_a == patch.card_id_b:
            return _fail("Cannot swap a card with itself")
        return _ok()

    if isinstance(patch, ResizeCardPatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        if not is_valid_position(patch.new_size):
            return _fail("new_size out of bounds")
        return _ok()

    if isinstance(patch, ChangeColorPatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        if not HEX_COLOR_RE.match(patch.color):
            return _fail(f"color must be #rrggbb, got '{patch.color}'")
        return _ok()

    if isinstance(patch, ChangeTitlePatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        if not patch.new_title.strip():
            return _fail("new_title cannot be empty")
        if patch.new_title in new_titles:
            return _fail(f"title '{patch.new_title}' already used")
        new_titles.add(patch.new_title)
        return _ok()

    if isinstance(patch, ChangeChartTypePatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        if patch.new_type not in VALID_CHART_TYPES:
            return _fail(f"invalid type '{patch.new_type}'")
        return _ok()

    if isinstance(patch, UpdateSqlPatch):
        if find_card(state, patch.card_id) is None:
            return _fail(f"card '{patch.card_id}' not found")
        err = _is_safe_sql(patch.new_sql)
        if err:
            return _fail(err)
        return _ok()

    if isinstance(patch, AddFilterPatch):
        page = find_page(state, patch.page_id)
        if not page:
            return _fail(f"page_id '{patch.page_id}' not found")
        if find_filter(state, patch.filter.id) is not None:
            return _fail(f"filter id '{patch.filter.id}' already exists")
        if not patch.filter.column:
            return _fail("filter.column is required")
        if isinstance(patch.apply_to, list):
            for cid in patch.apply_to:
                if find_card(state, cid) is None:
                    return _fail(f"apply_to card '{cid}' not found")
        return _ok()

    if isinstance(patch, RemoveFilterPatch):
        if find_filter(state, patch.filter_id) is None:
            return _fail(f"filter '{patch.filter_id}' not found")
        return _ok()

    if isinstance(patch, RollbackToVersionPatch):
        if patch.target_version < 1:
            return _fail("target_version must be >= 1")
        if patch.target_version == state.version:
            return _fail("target_version equals current version")
        return _ok()

    return _fail(f"Unknown patch type: {type(patch).__name__}")


def validate(patch: Any, state: DashboardState) -> ValidationResult:
    """
    Validate a patch (single or composite) against the current state.
    """
    # Seed uniqueness with existing titles
    existing_titles = set()
    for page in state.pages:
        for card in page.cards:
            existing_titles.add(card.title)

    if isinstance(patch, CompositePatch):
        titles = set(existing_titles)
        for sub in patch.patches:
            result = _validate_single(sub, state, titles)
            if not result.valid:
                return result
        return _ok()

    return _validate_single(patch, state, existing_titles)