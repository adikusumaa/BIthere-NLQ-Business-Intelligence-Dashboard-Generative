"""
Tests for patch_applier + preservation checker.
"""

import pytest

from app.dashboard.patch_applier import apply, PatchApplyError
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
from app.dashboard.preservation import verify_preservation
from app.dashboard.state_model import (
    Card,
    DashboardFilter,
    DashboardState,
    Page,
    Position,
)


def _card(cid, title="C", typ="bar", r=0, c=0, sx=6, sy=3, sql=None, color=None):
    style = {"color": color} if color else {}
    return Card(
        id=cid, title=title, type=typ, sql=sql,
        position=Position(row=r, col=c, size_x=sx, size_y=sy),
        style=style,
    )


def _state() -> DashboardState:
    return DashboardState(
        dashboard_id="d1",
        workspace_id="w1",
        version=3,
        parent_version=2,
        pages=[
            Page(
                id="p1",
                name="P",
                cards=[
                    _card("c-a", title="A", r=0, c=0),
                    _card("c-b", title="B", r=0, c=6),
                ],
                filters=[
                    DashboardFilter(id="f-1", name="F", type="category", column="t.col"),
                ],
            ),
        ],
    )


# =====================================================
# ADD_CARD
# =====================================================

def test_apply_add_card_appends():
    state = _state()
    patch = AddCardPatch(page_id="p1", card=_card("c-new", title="New", r=3, c=0))
    new_state, actions = apply(state, patch)

    assert new_state.version == 4
    assert any(c.id == "c-new" for c in new_state.pages[0].cards)
    assert len(state.pages[0].cards) == 2  # original untouched (deepcopy)

    action_types = [a["action"] for a in actions]
    assert "create_card" in action_types


def test_apply_add_card_insert_before():
    state = _state()
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-x", title="X", r=0, c=6, sx=6, sy=3),
        insert_before="c-b",
    )
    new_state, _ = apply(state, patch)
    ids = [c.id for c in new_state.pages[0].cards]
    assert ids.index("c-x") < ids.index("c-b")


def test_apply_add_card_auto_shift_on_overlap():
    state = _state()
    # c-a at (0,0,6x3). New card overlaps.
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="N", r=0, c=0),
    )
    new_state, actions = apply(state, patch)
    shifted = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert shifted.position.row >= 3


# =====================================================
# REMOVE_CARD
# =====================================================

def test_apply_remove_card():
    state = _state()
    patch = RemoveCardPatch(card_id="c-a")
    new_state, actions = apply(state, patch)

    ids = [c.id for c in new_state.pages[0].cards]
    assert "c-a" not in ids
    assert any(a["action"] == "delete_dashcard" for a in actions)


def test_apply_remove_missing_card_raises():
    with pytest.raises(PatchApplyError):
        apply(_state(), RemoveCardPatch(card_id="nope"))


# =====================================================
# MOVE / SWAP / RESIZE
# =====================================================

def test_apply_move_card():
    patch = MoveCardPatch(
        card_id="c-a",
        new_position=Position(row=5, col=0, size_x=6, size_y=3),
    )
    new_state, actions = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.position.row == 5
    assert any(a["action"] == "update_dashcard_position" for a in actions)


def test_apply_swap_cards():
    patch = SwapCardsPatch(card_id_a="c-a", card_id_b="c-b")
    new_state, _ = apply(_state(), patch)
    a = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    b = next(c for c in new_state.pages[0].cards if c.id == "c-b")
    assert a.position.row == 0 and a.position.col == 6
    assert b.position.row == 0 and b.position.col == 0


def test_apply_resize():
    patch = ResizeCardPatch(
        card_id="c-a",
        new_size=Position(row=0, col=0, size_x=12, size_y=4),
    )
    new_state, _ = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.position.size_x == 12


# =====================================================
# STYLE / TITLE / TYPE / SQL
# =====================================================

def test_apply_change_color():
    patch = ChangeColorPatch(card_id="c-a", color="#ef4444")
    new_state, _ = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.style.color == "#ef4444"


def test_apply_change_title():
    patch = ChangeTitlePatch(card_id="c-a", new_title="Renamed")
    new_state, _ = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.title == "Renamed"


def test_apply_change_type():
    patch = ChangeChartTypePatch(card_id="c-a", new_type="line")
    new_state, _ = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.type == "line"


def test_apply_update_sql():
    patch = UpdateSqlPatch(card_id="c-a", new_sql="SELECT 1")
    new_state, _ = apply(_state(), patch)
    card = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert card.sql == "SELECT 1"


# =====================================================
# FILTERS
# =====================================================

def test_apply_add_filter():
    new_filter = DashboardFilter(id="f-2", name="X", type="category", column="t.x")
    patch = AddFilterPatch(page_id="p1", filter=new_filter)
    new_state, actions = apply(_state(), patch)
    ids = [f.id for f in new_state.pages[0].filters]
    assert "f-2" in ids
    assert any(a["action"] == "add_dashboard_filter" for a in actions)


def test_apply_remove_filter():
    patch = RemoveFilterPatch(filter_id="f-1")
    new_state, actions = apply(_state(), patch)
    ids = [f.id for f in new_state.pages[0].filters]
    assert "f-1" not in ids
    assert any(a["action"] == "remove_dashboard_filter" for a in actions)


# =====================================================
# ROLLBACK rejected
# =====================================================

def test_apply_rollback_rejected():
    with pytest.raises(PatchApplyError):
        apply(_state(), RollbackToVersionPatch(target_version=1))


# =====================================================
# COMPOSITE
# =====================================================

def test_apply_composite():
    patch = CompositePatch(patches=[
        ChangeColorPatch(card_id="c-a", color="#000000"),
        RemoveCardPatch(card_id="c-b"),
    ])
    new_state, actions = apply(_state(), patch)
    a = next(c for c in new_state.pages[0].cards if c.id == "c-a")
    assert a.style.color == "#000000"
    ids = [c.id for c in new_state.pages[0].cards]
    assert "c-b" not in ids
    assert new_state.version == 4


# =====================================================
# Preservation
# =====================================================

def test_preservation_color_change_preserves_others():
    state = _state()
    patch = ChangeColorPatch(card_id="c-a", color="#000000")
    new_state, _ = apply(state, patch)
    violations = verify_preservation(state, new_state, patch)
    assert violations == []


def test_preservation_remove_card_preserves_others():
    state = _state()
    patch = RemoveCardPatch(card_id="c-a")
    new_state, _ = apply(state, patch)
    violations = verify_preservation(state, new_state, patch)
    assert violations == []


def test_preservation_add_card_auto_shift_allowed():
    state = _state()
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="New", r=0, c=0),
    )
    new_state, _ = apply(state, patch)
    violations = verify_preservation(state, new_state, patch, allow_position_shifts=True)
    assert violations == []


def test_preservation_detects_unexpected_change():
    state = _state()
    patch = ChangeColorPatch(card_id="c-a", color="#000000")
    new_state, _ = apply(state, patch)

    # Manually tamper with c-b's title
    tampered = next(c for c in new_state.pages[0].cards if c.id == "c-b")
    tampered.title = "TAMPERED"

    violations = verify_preservation(state, new_state, patch)
    assert any("c-b" in v for v in violations)