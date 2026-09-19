"""
Unit tests for DashboardState + Patch models.
"""

import pytest
from pydantic import ValidationError

from app.dashboard.state_model import (
    Card,
    CardStyle,
    DashboardFilter,
    DashboardState,
    Page,
    Position,
    all_card_ids,
    find_card,
    find_filter,
    find_page_of_card,
)
from app.dashboard.patch_model import (
    AddCardPatch,
    ChangeColorPatch,
    CompositePatch,
    MoveCardPatch,
    Patch,
    RemoveCardPatch,
    RollbackToVersionPatch,
    SwapCardsPatch,
    parse_patch,
)


def _sample_state() -> DashboardState:
    return DashboardState(
        dashboard_id="dash-1",
        workspace_id="ws-1",
        version=1,
        pages=[
            Page(
                id="page-1",
                name="Overview",
                cards=[
                    Card(id="card-a", title="A", type="scalar", position=Position(row=0, col=0)),
                    Card(id="card-b", title="B", type="bar", position=Position(row=0, col=6)),
                ],
                filters=[
                    DashboardFilter(id="f-1", name="Brand", type="category", column="cards.card_brand"),
                ],
            ),
        ],
    )


# =====================================================
# State helpers
# =====================================================

def test_find_card():
    state = _sample_state()
    assert find_card(state, "card-a").title == "A"
    assert find_card(state, "nope") is None


def test_find_page_of_card():
    state = _sample_state()
    assert find_page_of_card(state, "card-b").id == "page-1"
    assert find_page_of_card(state, "nope") is None


def test_find_filter():
    state = _sample_state()
    assert find_filter(state, "f-1").name == "Brand"
    assert find_filter(state, "nope") is None


def test_all_card_ids():
    state = _sample_state()
    assert set(all_card_ids(state)) == {"card-a", "card-b"}


def test_position_bounds():
    with pytest.raises(ValidationError):
        Position(col=25)  # > 23

    with pytest.raises(ValidationError):
        Position(size_x=1)  # < 2


# =====================================================
# Patch model parsing
# =====================================================

def test_parse_add_card():
    patch = parse_patch({
        "patch_type": "ADD_CARD",
        "page_id": "page-1",
        "card": {
            "id": "card-c",
            "title": "C",
            "type": "line",
            "position": {"row": 3, "col": 0, "size_x": 12, "size_y": 4},
        },
    })
    assert isinstance(patch, AddCardPatch)
    assert patch.card.id == "card-c"


def test_parse_remove_card():
    patch = parse_patch({"patch_type": "REMOVE_CARD", "card_id": "card-a"})
    assert isinstance(patch, RemoveCardPatch)


def test_parse_swap_cards():
    patch = parse_patch({
        "patch_type": "SWAP_CARDS",
        "card_id_a": "card-a",
        "card_id_b": "card-b",
    })
    assert isinstance(patch, SwapCardsPatch)


def test_parse_change_color():
    patch = parse_patch({
        "patch_type": "CHANGE_COLOR",
        "card_id": "card-a",
        "color": "#ef4444",
    })
    assert isinstance(patch, ChangeColorPatch)
    assert patch.color == "#ef4444"


def test_parse_move_card():
    patch = parse_patch({
        "patch_type": "MOVE_CARD",
        "card_id": "card-a",
        "new_position": {"row": 0, "col": 12, "size_x": 6, "size_y": 3},
    })
    assert isinstance(patch, MoveCardPatch)


def test_parse_rollback():
    patch = parse_patch({"patch_type": "ROLLBACK_TO_VERSION", "target_version": 4})
    assert isinstance(patch, RollbackToVersionPatch)


def test_parse_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown patch_type"):
        parse_patch({"patch_type": "NOT_A_PATCH"})


def test_parse_missing_type_raises():
    with pytest.raises(ValueError, match="Missing 'patch_type'"):
        parse_patch({})


# =====================================================
# Composite
# =====================================================

def test_composite_parses_inner():
    patch = parse_patch({
        "patch_type": "COMPOSITE",
        "patches": [
            {"patch_type": "REMOVE_CARD", "card_id": "card-a"},
            {"patch_type": "CHANGE_COLOR", "card_id": "card-b", "color": "#000000"},
        ],
    })
    assert isinstance(patch, CompositePatch)
    assert len(patch.patches) == 2


def test_composite_rejects_nested():
    with pytest.raises(ValidationError, match="Nested COMPOSITE"):
        CompositePatch(patches=[
            CompositePatch(patches=[
                RemoveCardPatch(card_id="x"),
            ]),
        ])