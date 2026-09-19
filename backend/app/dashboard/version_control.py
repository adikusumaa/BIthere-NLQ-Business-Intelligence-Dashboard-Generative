"""
Version control: rollback + diff + reverse patch construction.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.dashboard.patch_model import (
    AddCardPatch,
    ChangeColorPatch,
    ChangeTitlePatch,
    MoveCardPatch,
    RemoveCardPatch,
    RollbackToVersionPatch,
)
from app.dashboard.state_model import (
    DashboardState,
    all_card_ids,
    find_card,
)
from app.dashboard import state_store


class VersionControlError(Exception):
    """Raised when a version operation fails."""


def diff_states(
    state_a: DashboardState,
    state_b: DashboardState,
) -> Dict[str, Any]:
    """
    Produce a coarse diff between two states: cards added/removed/moved/modified,
    and page structure changes.
    """
    a_cards = {c.id: c for p in state_a.pages for c in p.cards}
    b_cards = {c.id: c for p in state_b.pages for c in p.cards}

    added = [cid for cid in b_cards if cid not in a_cards]
    removed = [cid for cid in a_cards if cid not in b_cards]
    moved: List[str] = []
    modified: List[Dict[str, str]] = []

    for cid in a_cards.keys() & b_cards.keys():
        ca, cb = a_cards[cid], b_cards[cid]
        if ca.position != cb.position:
            moved.append(cid)
        for field in ("title", "type", "sql"):
            if getattr(ca, field) != getattr(cb, field):
                modified.append({"card_id": cid, "field": field})
        if ca.style != cb.style:
            modified.append({"card_id": cid, "field": "style"})

    return {
        "from_version": state_a.version,
        "to_version": state_b.version,
        "added": added,
        "removed": removed,
        "moved": moved,
        "modified": modified,
    }


async def rollback(
    dashboard_id: str,
    target_version: int,
    user_id: Optional[str] = None,
) -> DashboardState:
    """
    Load target version, mark as new version on top of current.
    Returns the new state (version = current + 1, parent = current).
    """
    current = await state_store.load_latest(dashboard_id)
    if target_version == current.version:
        raise VersionControlError("Target version equals current version")

    target_state = await state_store.load_version(dashboard_id, target_version)

    # Create a new state that content-wise equals target,
    # but with version numbering continuing from current.
    new_state = deepcopy(target_state)
    new_state.parent_version = current.version
    new_state.version = current.version + 1

    rollback_patch = RollbackToVersionPatch(target_version=target_version)

    await state_store.save_version(
        dashboard_id=dashboard_id,
        state=new_state,
        patch=rollback_patch,
        user_id=user_id,
        from_version=current.version,
    )

    logger.info(
        f"[SUCCESS] Rollback: {dashboard_id} from v{current.version} "
        f"to v{new_state.version} (content = v{target_version})"
    )
    return new_state