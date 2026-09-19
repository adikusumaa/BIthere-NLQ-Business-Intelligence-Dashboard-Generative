"""
Diff two DashboardStates and produce abstract Metabase actions to
transform `from_state` into `to_state`. Used by undo endpoint.
"""

from typing import Any, Dict, List

from app.dashboard.state_model import DashboardState, find_card


def diff_to_actions(
    from_state: DashboardState,
    to_state: DashboardState,
) -> List[Dict[str, Any]]:
    """
    Produce a list of actions that would move from_state toward to_state
    (used for undo — restoring a previous version).
    """
    actions: List[Dict[str, Any]] = []

    from_cards = {c.id: c for p in from_state.pages for c in p.cards}
    to_cards = {c.id: c for p in to_state.pages for c in p.cards}

    # Cards in `to` but not in `from` -> need to create
    for cid, card in to_cards.items():
        if cid not in from_cards:
            actions.append({
                "action": "create_card",
                "card_id": card.id,
                "title": card.title,
                "chart_type": card.type,
                "sql": card.sql,
                "style": card.style.model_dump() if card.style else {},
            })
            actions.append({
                "action": "attach_card_to_dashboard",
                "card_id": card.id,
                "position": card.position.model_dump(),
            })

    # Cards in `from` but not in `to` -> delete
    for cid, card in from_cards.items():
        if cid not in to_cards:
            actions.append({
                "action": "delete_dashcard",
                "card_id": card.id,
                "dashcard_id": card.metabase.dashcard_id,
            })

    # Cards in both -> check differences
    for cid in from_cards.keys() & to_cards.keys():
        old = from_cards[cid]
        new = to_cards[cid]

        if old.position != new.position:
            actions.append({
                "action": "update_dashcard_position",
                "card_id": new.id,
                "dashcard_id": new.metabase.dashcard_id,
                "position": new.position.model_dump(),
            })

        if old.title != new.title:
            actions.append({
                "action": "update_card_name",
                "card_id": new.id,
                "metabase_card_id": new.metabase.card_id,
                "title": new.title,
            })

        if old.type != new.type:
            actions.append({
                "action": "update_card_display",
                "card_id": new.id,
                "metabase_card_id": new.metabase.card_id,
                "display": new.type,
            })

        if old.sql != new.sql and new.sql:
            actions.append({
                "action": "update_card_sql",
                "card_id": new.id,
                "metabase_card_id": new.metabase.card_id,
                "sql": new.sql,
            })

        if old.style != new.style:
            actions.append({
                "action": "update_card_style",
                "card_id": new.id,
                "metabase_card_id": new.metabase.card_id,
                "style": new.style.model_dump() if new.style else {},
            })

    return actions