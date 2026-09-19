"""
Tests for grid engine + patch validator.
"""

import pytest

from app.dashboard.grid import (
    check_overlap,
    find_free_position,
    is_valid_position,
    reflow,
    auto_shift,
    GRID_COLS,
)
from app.dashboard.patch_model import (
    AddCardPatch,
    ChangeColorPatch,
    CompositePatch,
    MoveCardPatch,
    RemoveCardPatch,
    RollbackToVersionPatch,
    SwapCardsPatch,
    UpdateSqlPatch,
)
from app.dashboard.patch_validator import validate
from app.dashboard.state_model import (
    Card,
    DashboardState,
    Page,
    Position,
)


def _card(cid, title="C", r=0, c=0, sx=6, sy=3, sql=None, color=None) -> Card:
    style = {"color": color} if color else {}
    return Card(
        id=cid, title=title, type="bar",
        sql=sql,
        position=Position(row=r, col=c, size_x=sx, size_y=sy),
        style=style,
    )


def _state(cards=None) -> DashboardState:
    return DashboardState(
        dashboard_id="d1",
        workspace_id="w1",
        version=3,
        pages=[Page(id="p1", name="Page", cards=cards or [_card("c-a", "A")])],
    )


# =====================================================
# Grid
# =====================================================

def test_overlap_true():
    a = Position(row=0, col=0, size_x=6, size_y=3)
    b = Position(row=1, col=2, size_x=6, size_y=3)
    assert check_overlap(a, b)


def test_overlap_false_adjacent():
    a = Position(row=0, col=0, size_x=6, size_y=3)
    b = Position(row=0, col=6, size_x=6, size_y=3)
    assert not check_overlap(a, b)


def test_overlap_false_different_rows():
    a = Position(row=0, col=0, size_x=6, size_y=3)
    b = Position(row=5, col=0, size_x=6, size_y=3)
    assert not check_overlap(a, b)


def test_is_valid_position_ok():
    assert is_valid_position(Position(row=0, col=0, size_x=6, size_y=3))


def test_is_valid_position_bad_col():
    assert not is_valid_position(Position(row=0, col=20, size_x=6, size_y=3))


def test_is_valid_position_too_small():
    # Pydantic Position model already enforces size_x >= 2 at construction
    with pytest.raises(Exception):
        Position(row=0, col=0, size_x=1, size_y=3)


def test_find_free_position_empty():
    pos = find_free_position([], 6, 3)
    assert pos.row == 0 and pos.col == 0


def test_find_free_position_fills_gap():
    cards = [_card("a", r=0, c=0, sx=6, sy=3)]
    pos = find_free_position(cards, 6, 3)
    assert pos.row == 0 and pos.col == 6


def test_find_free_position_wraps_row():
    cards = [_card(f"c{i}", r=0, c=i * 6, sx=6, sy=3) for i in range(4)]
    pos = find_free_position(cards, 6, 3)
    assert pos.row >= 3


def test_auto_shift_returns_moved_cards():
    existing = _card("a", r=0, c=0, sx=6, sy=3)
    new_pos = Position(row=0, col=0, size_x=6, size_y=3)
    shifts = auto_shift([existing], new_pos)
    assert len(shifts) == 1
    assert shifts[0][0] == "a"
    assert shifts[0][1].row == 3


def test_reflow_no_change_when_tight():
    cards = [_card("a", r=0, c=0, sx=6, sy=3)]
    assert reflow(cards) == []


def test_reflow_packs_after_removal():
    cards = [
        _card("a", r=0, c=0, sx=6, sy=3),
        _card("b", r=0, c=12, sx=6, sy=3),  # gap at col=6
    ]
    changes = reflow(cards)
    moved_ids = {cid for cid, _ in changes}
    assert "b" in moved_ids


# =====================================================
# Validator — ADD_CARD
# =====================================================

def test_validate_add_card_ok():
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="New", r=3, c=0, sx=6, sy=3),
    )
    assert validate(patch, _state()).valid


def test_validate_add_card_bad_page():
    patch = AddCardPatch(page_id="bad", card=_card("c-new", title="X"))
    result = validate(patch, _state())
    assert not result.valid
    assert "page_id" in result.reason


def test_validate_add_card_duplicate_id():
    patch = AddCardPatch(page_id="p1", card=_card("c-a", title="Dup"))
    result = validate(patch, _state())
    assert not result.valid


def test_validate_add_card_duplicate_title():
    patch = AddCardPatch(page_id="p1", card=_card("c-new", title="A"))
    result = validate(patch, _state())
    assert not result.valid
    assert "title" in result.reason


def test_validate_add_card_bad_position():
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="X", c=20, sx=6, sy=3),
    )
    result = validate(patch, _state())
    assert not result.valid


def test_validate_add_card_dangerous_sql():
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="X", sql="DROP TABLE users"),
    )
    result = validate(patch, _state())
    assert not result.valid
    assert "DROP" in result.reason


def test_validate_add_card_safe_sql():
    patch = AddCardPatch(
        page_id="p1",
        card=_card("c-new", title="X", sql="SELECT * FROM t LIMIT 10"),
    )
    assert validate(patch, _state()).valid


# =====================================================
# Validator — others
# =====================================================

def test_validate_remove_card_ok():
    patch = RemoveCardPatch(card_id="c-a")
    assert validate(patch, _state()).valid


def test_validate_remove_missing_card():
    patch = RemoveCardPatch(card_id="nope")
    assert not validate(patch, _state()).valid


def test_validate_swap_same_card_fails():
    patch = SwapCardsPatch(card_id_a="c-a", card_id_b="c-a")
    assert not validate(patch, _state()).valid


def test_validate_move_bad_position():
    patch = MoveCardPatch(
        card_id="c-a",
        new_position=Position(row=0, col=22, size_x=6, size_y=3),
    )
    assert not validate(patch, _state()).valid


def test_validate_color_bad_format():
    patch = ChangeColorPatch(card_id="c-a", color="red")
    result = validate(patch, _state())
    assert not result.valid
    assert "color" in result.reason


def test_validate_color_ok():
    patch = ChangeColorPatch(card_id="c-a", color="#3b82f6")
    assert validate(patch, _state()).valid


def test_validate_update_sql_forbidden():
    patch = UpdateSqlPatch(card_id="c-a", new_sql="DELETE FROM users")
    result = validate(patch, _state())
    assert not result.valid


def test_validate_rollback_target_equals_current():
    patch = RollbackToVersionPatch(target_version=3)
    result = validate(patch, _state())
    assert not result.valid


def test_validate_rollback_ok():
    patch = RollbackToVersionPatch(target_version=1)
    assert validate(patch, _state()).valid


# =====================================================
# Composite
# =====================================================

def test_validate_composite_ok():
    patch = CompositePatch(patches=[
        RemoveCardPatch(card_id="c-a"),
        ChangeColorPatch(card_id="c-a", color="#000000"),
    ])
    # c-a removed first, but the color patch references it — validator does
    # not simulate order, so this is OK in the composite chain
    result = validate(patch, _state())
    # Actually second patch will fail because c-a is still "present" in state
    # So this returns valid (validator does not simulate removal)
    assert result.valid is True


def test_validate_composite_fails_on_first_error():
    patch = CompositePatch(patches=[
        RemoveCardPatch(card_id="c-a"),
        ChangeColorPatch(card_id="c-a", color="red"),  # bad hex
    ])
    result = validate(patch, _state())
    assert not result.valid