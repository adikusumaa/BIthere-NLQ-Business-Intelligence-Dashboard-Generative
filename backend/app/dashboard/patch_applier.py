"""
Patch applier: apply a validated patch to a DashboardState copy.
Returns the new state plus a list of abstract Metabase actions that
the metabase_adapter will translate into API calls.
"""

import uuid
from copy import deepcopy
from typing import Any, Dict, List, Tuple

from app.core.logging import logger
from app.dashboard.grid import auto_shift, reflow
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
    find_card,
    find_filter,
    find_page,
    find_page_of_card,
)


class PatchApplyError(Exception):
    """Raised when a patch cannot be applied."""


def _new_card_id() -> str:
    return f"card-{uuid.uuid4().hex[:8]}"


def _actions_for_card_create(card) -> List[Dict[str, Any]]:
    return [
        {
            "action": "create_card",
            "card_id": card.id,
            "title": card.title,
            "chart_type": card.type,
            "sql": card.sql,
            "style": card.style.model_dump(),
        },
        {
            "action": "attach_card_to_dashboard",
            "card_id": card.id,
            "position": card.position.model_dump(),
        },
    ]


def _actions_for_card_delete(card) -> List[Dict[str, Any]]:
    return [
        {
            "action": "delete_dashcard",
            "card_id": card.id,
            "dashcard_id": card.metabase.dashcard_id,
        }
    ]


def _actions_for_card_move(card) -> List[Dict[str, Any]]:
    return [
        {
            "action": "update_dashcard_position",
            "card_id": card.id,
            "dashcard_id": card.metabase.dashcard_id,
            "position": card.position.model_dump(),
        }
    ]


def _apply_single(state: DashboardState, patch: Any) -> List[Dict[str, Any]]:
    """Apply one non-composite patch in place. Returns action list."""
    actions: List[Dict[str, Any]] = []

    if isinstance(patch, AddCardPatch):
        page = find_page(state, patch.page_id)
        if not page:
            raise PatchApplyError(f"page {patch.page_id} not found")

        # Auto-assign position if not given (default 0,0) — find free slot
        card = patch.card
        if not card.id:
            card.id = _new_card_id()

        # Auto-shift existing cards that overlap
        shifts = auto_shift(page.cards, card.position)
        for card_id, new_pos in shifts:
            existing = find_card(state, card_id)
            if existing:
                existing.position = new_pos
                actions.append({
                    "action": "update_dashcard_position",
                    "card_id": existing.id,
                    "dashcard_id": existing.metabase.dashcard_id,
                    "position": new_pos.model_dump(),
                })

        # Insert relative to target card if requested
        if patch.insert_before:
            idx = next(
                (i for i, c in enumerate(page.cards) if c.id == patch.insert_before),
                len(page.cards),
            )
            page.cards.insert(idx, card)
        elif patch.insert_after:
            idx = next(
                (i for i, c in enumerate(page.cards) if c.id == patch.insert_after),
                len(page.cards) - 1,
            )
            page.cards.insert(idx + 1, card)
        else:
            page.cards.append(card)

        actions = _actions_for_card_create(card) + actions

    elif isinstance(patch, RemoveCardPatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        page = find_page_of_card(state, patch.card_id)
        if not page:
            raise PatchApplyError("card has no page")

        actions.extend(_actions_for_card_delete(card))
        page.cards = [c for c in page.cards if c.id != patch.card_id]

        # Reflow remaining cards
        for card_id, new_pos in reflow(page.cards):
            moved = find_card(state, card_id)
            if moved:
                moved.position = new_pos
                actions.append({
                    "action": "update_dashcard_position",
                    "card_id": moved.id,
                    "dashcard_id": moved.metabase.dashcard_id,
                    "position": new_pos.model_dump(),
                })

    elif isinstance(patch, MoveCardPatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.position = patch.new_position
        actions.extend(_actions_for_card_move(card))

    elif isinstance(patch, SwapCardsPatch):
        a = find_card(state, patch.card_id_a)
        b = find_card(state, patch.card_id_b)
        if not a or not b:
            raise PatchApplyError("one of the cards not found")
        a.position, b.position = b.position, a.position
        actions.extend(_actions_for_card_move(a))
        actions.extend(_actions_for_card_move(b))

    elif isinstance(patch, ResizeCardPatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.position = patch.new_size
        actions.extend(_actions_for_card_move(card))

    elif isinstance(patch, ChangeColorPatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.style.color = patch.color
        actions.append({
            "action": "update_card_style",
            "card_id": card.id,
            "metabase_card_id": card.metabase.card_id,
            "style": card.style.model_dump(),
        })

    elif isinstance(patch, ChangeTitlePatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.title = patch.new_title
        actions.append({
            "action": "update_card_name",
            "card_id": card.id,
            "metabase_card_id": card.metabase.card_id,
            "title": card.title,
        })

    elif isinstance(patch, ChangeChartTypePatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.type = patch.new_type
        actions.append({
            "action": "update_card_display",
            "card_id": card.id,
            "metabase_card_id": card.metabase.card_id,
            "display": card.type,
        })

    elif isinstance(patch, UpdateSqlPatch):
        card = find_card(state, patch.card_id)
        if not card:
            raise PatchApplyError(f"card {patch.card_id} not found")
        card.sql = patch.new_sql
        actions.append({
            "action": "update_card_sql",
            "card_id": card.id,
            "metabase_card_id": card.metabase.card_id,
            "sql": card.sql,
        })

    elif isinstance(patch, AddFilterPatch):
        page = find_page(state, patch.page_id)
        if not page:
            raise PatchApplyError(f"page {patch.page_id} not found")

        page.filters.append(patch.filter)

        # Bind to cards
        target_card_ids = (
            [c.id for c in page.cards]
            if patch.apply_to == "all"
            else patch.apply_to
        )
        for card in page.cards:
            if card.id in target_card_ids:
                if patch.filter.id not in card.filters_applied:
                    card.filters_applied.append(patch.filter.id)

        actions.append({
            "action": "add_dashboard_filter",
            "page_id": page.id,
            "filter": patch.filter.model_dump(),
            "apply_to": target_card_ids,
        })

    elif isinstance(patch, RemoveFilterPatch):
        page = find_page(state, patch.filter_id) or None
        # find page containing filter
        from app.dashboard.state_model import find_page_of_filter
        page = find_page_of_filter(state, patch.filter_id)
        if not page:
            raise PatchApplyError(f"filter {patch.filter_id} not found")

        page.filters = [f for f in page.filters if f.id != patch.filter_id]
        for card in page.cards:
            card.filters_applied = [
                fid for fid in card.filters_applied if fid != patch.filter_id
            ]
        actions.append({
            "action": "remove_dashboard_filter",
            "filter_id": patch.filter_id,
        })

    elif isinstance(patch, RollbackToVersionPatch):
        # Handled by version_control layer, not by applier
        raise PatchApplyError(
            "ROLLBACK_TO_VERSION must be handled by version_control, "
            "not by patch_applier"
        )

    else:
        raise PatchApplyError(f"Unsupported patch: {type(patch).__name__}")

    return actions


def apply(state: DashboardState, patch: Any) -> Tuple[DashboardState, List[Dict[str, Any]]]:
    """
    Apply a patch to a deep-copied state.

    Args:
        state: current DashboardState.
        patch: patch instance (single or CompositePatch).

    Returns:
        (new_state, actions) — new state with `version` incremented,
        plus a list of abstract Metabase actions.
    """
    new_state = deepcopy(state)
    actions: List[Dict[str, Any]] = []

    if isinstance(patch, CompositePatch):
        for sub in patch.patches:
            actions.extend(_apply_single(new_state, sub))
    else:
        actions = _apply_single(new_state, patch)

    # Increment version
    new_state.parent_version = state.version
    new_state.version = state.version + 1

    logger.info(
        f"[SUCCESS] Patch {type(patch).__name__} applied: "
        f"v{state.version} -> v{new_state.version}, {len(actions)} actions"
    )
    return new_state, actions