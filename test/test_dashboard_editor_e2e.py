"""
End-to-end test for F-13 Iterative Dashboard Editor.
Simulates 7 iterations: create → add → swap → color → filter → remove → rollback.
Uses mocked LLM for the intent parser, real Supabase for state store.
"""

import json
import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.dashboard import (
    intent_parser,
    state_store,
    undo_redo,
    version_control,
)
from app.dashboard.patch_applier import apply
from app.dashboard.patch_model import parse_patch
from app.dashboard.patch_validator import validate
from app.dashboard.state_model import (
    Card,
    CardStyle,
    DashboardState,
    Page,
    Position,
)
from app.workspace import service as ws_service


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"E2E F13 {uuid.uuid4().hex[:6]}")
    yield ws
    await ws_service.delete_workspace(ws["id"], owner)


def _initial_state(workspace_id: str, dashboard_id: str) -> DashboardState:
    """Iteration 1: initial dashboard with 3 charts."""
    return DashboardState(
        dashboard_id=dashboard_id,
        workspace_id=workspace_id,
        version=1,
        pages=[
            Page(
                id="page-1",
                name="Overview",
                cards=[
                    Card(
                        id="card-kpi",
                        title="Total Fraud",
                        type="scalar",
                        position=Position(row=0, col=0, size_x=6, size_y=3),
                    ),
                    Card(
                        id="card-monthly",
                        title="Monthly Trend",
                        type="line",
                        position=Position(row=3, col=0, size_x=12, size_y=4),
                        style=CardStyle(color="#3b82f6"),
                    ),
                    Card(
                        id="card-top10",
                        title="Top 10 States",
                        type="bar",
                        position=Position(row=3, col=12, size_x=12, size_y=4),
                        style=CardStyle(color="#10b981"),
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def mock_llm():
    """
    Sequence of mocked LLM responses matching 7 iterations.
    Each response is a JSON patch string.
    """
    responses = [
        # Iter 2: ADD_CARD
        json.dumps({
            "patch_type": "ADD_CARD",
            "page_id": "page-1",
            "insert_before": "card-top10",
            "card": {
                "id": "card-by-brand",
                "title": "Fraud by Card Brand",
                "type": "bar",
                "position": {"row": 7, "col": 0, "size_x": 12, "size_y": 4},
                "style": {"color": "#3b82f6"},
            },
        }),
        # Iter 3: SWAP_CARDS
        json.dumps({
            "patch_type": "SWAP_CARDS",
            "card_id_a": "card-monthly",
            "card_id_b": "card-by-brand",
        }),
        # Iter 4: CHANGE_COLOR
        json.dumps({
            "patch_type": "CHANGE_COLOR",
            "card_id": "card-monthly",
            "color": "#ef4444",
        }),
        # Iter 5: ADD_FILTER
        json.dumps({
            "patch_type": "ADD_FILTER",
            "page_id": "page-1",
            "filter": {
                "id": "filter-brand",
                "name": "Card Brand",
                "type": "category",
                "column": "cards.card_brand",
            },
            "apply_to": "all",
        }),
        # Iter 6: REMOVE_CARD
        json.dumps({
            "patch_type": "REMOVE_CARD",
            "card_id": "card-top10",
        }),
        # Iter 7: ROLLBACK handled separately (not via LLM)
    ]

    with patch.object(intent_parser, "generate_chat", new_callable=AsyncMock) as mock:
        mock.side_effect = responses
        yield mock


async def test_full_iteration_workflow(workspace, mock_llm):
    """
    Full F-13 iteration workflow:
      1. Seed initial dashboard (v1)
      2. ADD_CARD → v2
      3. SWAP_CARDS → v3
      4. CHANGE_COLOR → v4
      5. ADD_FILTER → v5
      6. REMOVE_CARD → v6
      7. ROLLBACK to v3 → v7 (content = v3)
    """
    dashboard_id = str(uuid.uuid4())
    session_id = f"e2e-{uuid.uuid4().hex[:8]}"

    # Iteration 1: seed initial state
    state = _initial_state(workspace["id"], dashboard_id)
    await state_store.save_version(dashboard_id, state)
    assert (await state_store.load_latest(dashboard_id)).version == 1

    # Iteration 2: ADD_CARD
    instruction_2 = "Tambahkan chart bar di atas Top 10 States"
    patch_2 = await intent_parser.parse_instruction(
        instruction_2, state, api_key="fake"
    )
    assert patch_2.patch_type == "ADD_CARD"
    assert validate(patch_2, state).valid

    new_state, _ = apply(state, patch_2)
    await state_store.save_version(
        dashboard_id, new_state, patch=patch_2, from_version=state.version
    )
    await undo_redo.push_undo(session_id, patch_2)
    state = new_state
    assert state.version == 2
    assert any(c.id == "card-by-brand" for p in state.pages for c in p.cards)

    # Iteration 3: SWAP_CARDS
    patch_3 = await intent_parser.parse_instruction("Swap cards", state, api_key="fake")
    assert patch_3.patch_type == "SWAP_CARDS"
    assert validate(patch_3, state).valid

    new_state, _ = apply(state, patch_3)
    await state_store.save_version(
        dashboard_id, new_state, patch=patch_3, from_version=state.version
    )
    await undo_redo.push_undo(session_id, patch_3)
    state = new_state
    assert state.version == 3

    monthly = next(c for p in state.pages for c in p.cards if c.id == "card-monthly")
    by_brand = next(c for p in state.pages for c in p.cards if c.id == "card-by-brand")
    # After swap: monthly took by_brand's position
    assert monthly.position.row == 7

    # Capture state at v3 for later comparison
    v3_snapshot = state.model_dump(mode="json")

    # Iteration 4: CHANGE_COLOR
    patch_4 = await intent_parser.parse_instruction("Change color", state, api_key="fake")
    assert patch_4.patch_type == "CHANGE_COLOR"
    assert validate(patch_4, state).valid

    new_state, _ = apply(state, patch_4)
    await state_store.save_version(
        dashboard_id, new_state, patch=patch_4, from_version=state.version
    )
    await undo_redo.push_undo(session_id, patch_4)
    state = new_state
    assert state.version == 4

    monthly = next(c for p in state.pages for c in p.cards if c.id == "card-monthly")
    assert monthly.style.color == "#ef4444"

    # Iteration 5: ADD_FILTER
    patch_5 = await intent_parser.parse_instruction("Add filter", state, api_key="fake")
    assert patch_5.patch_type == "ADD_FILTER"
    assert validate(patch_5, state).valid

    new_state, _ = apply(state, patch_5)
    await state_store.save_version(
        dashboard_id, new_state, patch=patch_5, from_version=state.version
    )
    await undo_redo.push_undo(session_id, patch_5)
    state = new_state
    assert state.version == 5
    assert any(f.id == "filter-brand" for p in state.pages for f in p.filters)

    # Iteration 6: REMOVE_CARD
    patch_6 = await intent_parser.parse_instruction("Remove top10", state, api_key="fake")
    assert patch_6.patch_type == "REMOVE_CARD"
    assert validate(patch_6, state).valid

    new_state, _ = apply(state, patch_6)
    await state_store.save_version(
        dashboard_id, new_state, patch=patch_6, from_version=state.version
    )
    await undo_redo.push_undo(session_id, patch_6)
    state = new_state
    assert state.version == 6
    assert not any(c.id == "card-top10" for p in state.pages for c in p.cards)

    # Iteration 7: ROLLBACK to v3
    rolled_back = await version_control.rollback(
        dashboard_id, target_version=3, user_id=None
    )
    assert rolled_back.version == 7
    assert rolled_back.parent_version == 6

    # Verify content matches v3
    for orig_card in v3_snapshot["pages"][0]["cards"]:
        match = next(
            (c for p in rolled_back.pages for c in p.cards if c.id == orig_card["id"]),
            None,
        )
        assert match is not None, f"Card {orig_card['id']} missing after rollback"
        assert match.title == orig_card["title"]
        assert match.position.row == orig_card["position"]["row"]

    # Version history should have 7 entries
    history = await state_store.list_versions(dashboard_id)
    assert len(history) == 7

    # Patch log should record all applied patches
    patches = await state_store.get_patches(dashboard_id)
    patch_types = [p["patch_json"].get("patch_type") for p in patches]
    assert "ADD_CARD" in patch_types
    assert "SWAP_CARDS" in patch_types
    assert "CHANGE_COLOR" in patch_types
    assert "ADD_FILTER" in patch_types
    assert "REMOVE_CARD" in patch_types
    assert "ROLLBACK_TO_VERSION" in patch_types


async def test_preservation_across_iterations(workspace, mock_llm):
    """Verify non-targeted cards keep their properties across patches."""
    dashboard_id = str(uuid.uuid4())
    state = _initial_state(workspace["id"], dashboard_id)

    # Capture initial top10
    top10_original = next(
        c for p in state.pages for c in p.cards if c.id == "card-top10"
    ).model_dump(mode="json")

    # Apply CHANGE_COLOR to monthly
    patch = await intent_parser.parse_instruction("Change color", state, api_key="fake")
    new_state, _ = apply(state, patch)

    # top10 should be unchanged
    top10_after = next(
        c for p in new_state.pages for c in p.cards if c.id == "card-top10"
    )
    assert top10_after.title == top10_original["title"]
    assert top10_after.type == top10_original["type"]
    assert top10_after.position.row == top10_original["position"]["row"]


async def test_undo_stack_after_iterations(workspace, mock_llm):
    """Verify undo stack reflects the sequence of applied patches."""
    dashboard_id = str(uuid.uuid4())
    session_id = f"e2e-undo-{uuid.uuid4().hex[:6]}"

    state = _initial_state(workspace["id"], dashboard_id)

    # Apply 3 patches
    for _ in range(3):
        patch = await intent_parser.parse_instruction("do it", state, api_key="fake")
        new_state, _ = apply(state, patch)
        await undo_redo.push_undo(session_id, patch)
        state = new_state

    # Pop all three
    p1 = await undo_redo.undo(session_id)
    p2 = await undo_redo.undo(session_id)
    p3 = await undo_redo.undo(session_id)

    assert p1 is not None
    assert p2 is not None
    assert p3 is not None
    assert await undo_redo.undo(session_id) is None  # stack empty

    # Redo should restore them
    r1 = await undo_redo.redo(session_id)
    assert r1 is not None