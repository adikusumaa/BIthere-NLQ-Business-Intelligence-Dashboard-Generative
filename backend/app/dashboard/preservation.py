"""
Preservation checker: verify that a patch did not silently modify
parts of the state it was not supposed to touch.
"""

from typing import Any, List, Set

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
from app.dashboard.state_model import DashboardState, find_card


class PreservationViolation(Exception):
    """Raised when non-targeted fields changed unexpectedly."""


def _touched_card_ids(patch: Any) -> Set[str]:
    """Collect all card ids explicitly referenced by a patch."""
    ids: Set[str] = set()

    def _collect(p: Any):
        if isinstance(p, CompositePatch):
            for sub in p.patches:
                _collect(sub)
        elif isinstance(p, AddCardPatch):
            ids.add(p.card.id)
        elif isinstance(p, RemoveCardPatch):
            ids.add(p.card_id)
        elif isinstance(p, MoveCardPatch):
            ids.add(p.card_id)
        elif isinstance(p, SwapCardsPatch):
            ids.add(p.card_id_a)
            ids.add(p.card_id_b)
        elif isinstance(p, ResizeCardPatch):
            ids.add(p.card_id)
        elif isinstance(p, ChangeColorPatch):
            ids.add(p.card_id)
        elif isinstance(p, ChangeTitlePatch):
            ids.add(p.card_id)
        elif isinstance(p, ChangeChartTypePatch):
            ids.add(p.card_id)
        elif isinstance(p, UpdateSqlPatch):
            ids.add(p.card_id)

    _collect(patch)
    return ids


def _touched_filter_ids(patch: Any) -> Set[str]:
    ids: Set[str] = set()

    def _collect(p: Any):
        if isinstance(p, CompositePatch):
            for sub in p.patches:
                _collect(sub)
        elif isinstance(p, AddFilterPatch):
            ids.add(p.filter.id)
        elif isinstance(p, RemoveFilterPatch):
            ids.add(p.filter_id)

    _collect(patch)
    return ids


def _position_changed(old_state: DashboardState, new_state: DashboardState) -> Set[str]:
    """Return ids of cards whose positions changed."""
    changed: Set[str] = set()
    for old_page in old_state.pages:
        for old_card in old_page.cards:
            new_card = find_card(new_state, old_card.id)
            if new_card and new_card.position != old_card.position:
                changed.add(old_card.id)
    return changed


def verify_preservation(
    old_state: DashboardState,
    new_state: DashboardState,
    patch: Any,
    allow_position_shifts: bool = True,
) -> List[str]:
    """
    Verify that:
      - cards not referenced by the patch keep title/type/sql/style unchanged.
      - filters not referenced keep their definition.
      - pages structure is unchanged except for legitimate additions/removals.

    Position changes for non-targeted cards are tolerated when
    `allow_position_shifts` is True (auto-shift/reflow use case).

    Returns a list of violation strings (empty = passed).
    """
    violations: List[str] = []

    touched_cards = _touched_card_ids(patch)
    allowed_position_changes = (
        _position_changed(old_state, new_state) if allow_position_shifts else set()
    )

    # Check each old card that still exists
    for old_page in old_state.pages:
        for old_card in old_page.cards:
            new_card = find_card(new_state, old_card.id)
            if new_card is None:
                # Card removed. Only allowed if patch touched it.
                if old_card.id not in touched_cards:
                    violations.append(
                        f"Card '{old_card.id}' was removed but not targeted by patch"
                    )
                continue

            # Card still exists — check untouched fields
            if old_card.id not in touched_cards:
                if old_card.title != new_card.title:
                    violations.append(f"Card '{old_card.id}' title changed unexpectedly")
                if old_card.type != new_card.type:
                    violations.append(f"Card '{old_card.id}' type changed unexpectedly")
                if old_card.sql != new_card.sql:
                    violations.append(f"Card '{old_card.id}' sql changed unexpectedly")
                if old_card.style != new_card.style:
                    violations.append(f"Card '{old_card.id}' style changed unexpectedly")
                if (
                    old_card.position != new_card.position
                    and old_card.id not in allowed_position_changes
                ):
                    violations.append(
                        f"Card '{old_card.id}' position changed unexpectedly"
                    )

    # Check filters
    touched_filters = _touched_filter_ids(patch)
    old_filters = {f.id: f for p in old_state.pages for f in p.filters}
    new_filters = {f.id: f for p in new_state.pages for f in p.filters}

    for fid, old_f in old_filters.items():
        if fid not in touched_filters and fid in new_filters:
            if old_f != new_filters[fid]:
                violations.append(f"Filter '{fid}' changed unexpectedly")

    return violations