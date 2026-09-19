"""
Tests for Intent Parser + State Summarizer (mocked LLM).
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.dashboard import intent_parser
from app.dashboard.state_model import (
    Card,
    DashboardFilter,
    DashboardState,
    Page,
    Position,
)
from app.dashboard.state_summarizer import summarize_state
from app.dashboard.patch_model import (
    AddCardPatch,
    ChangeColorPatch,
    CompositePatch,
    RemoveCardPatch,
    SwapCardsPatch,
)


def _state() -> DashboardState:
    return DashboardState(
        dashboard_id="dash-1",
        workspace_id="ws-1",
        version=2,
        parent_version=1,
        pages=[
            Page(
                id="page-1",
                name="Overview",
                cards=[
                    Card(id="card-monthly", title="Monthly Trend", type="line",
                         position=Position(row=0, col=0, size_x=12, size_y=4)),
                    Card(id="card-top10", title="Top 10 States", type="bar",
                         position=Position(row=4, col=0, size_x=12, size_y=4),
                         style={"color": "#10b981"}),
                ],
                filters=[
                    DashboardFilter(id="f-1", name="Brand", type="category", column="cards.card_brand"),
                ],
            ),
        ],
    )


# =====================================================
# Summarizer
# =====================================================

def test_summarize_contains_page_and_cards():
    s = summarize_state(_state())
    assert "Page 'Overview'" in s
    assert "card_id=card-monthly" in s
    assert "title=\"Monthly Trend\"" in s
    assert "type=line" in s
    assert "card_id=card-top10" in s
    assert "color=#10b981" in s
    assert "filter_id=f-1" in s


def test_summarize_empty_state():
    empty = DashboardState(dashboard_id="x", workspace_id="y", version=1)
    s = summarize_state(empty)
    assert "Total pages: 0" in s


# =====================================================
# Intent Parser
# =====================================================

@pytest.fixture
def mock_generate_chat():
    with patch.object(intent_parser, "generate_chat", new_callable=AsyncMock) as m:
        yield m


@pytest.fixture
def mock_cache(monkeypatch):
    class FakeCache:
        def __init__(self):
            self.store = {}
        async def get(self, k):
            return self.store.get(k)
        async def set(self, k, v, ttl=None):
            self.store[k] = v
    fake = FakeCache()
    monkeypatch.setattr(intent_parser, "cache", fake)
    return fake


async def test_parse_add_card(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({
        "patch_type": "ADD_CARD",
        "page_id": "page-1",
        "card": {
            "id": "card-new",
            "title": "New Chart",
            "type": "bar",
            "position": {"row": 8, "col": 0, "size_x": 12, "size_y": 4},
        },
    })

    patch = await intent_parser.parse_instruction("Add a bar chart", _state())
    assert isinstance(patch, AddCardPatch)
    assert patch.card.title == "New Chart"


async def test_parse_remove_card(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({
        "patch_type": "REMOVE_CARD",
        "card_id": "card-top10",
    })

    patch = await intent_parser.parse_instruction("Hapus Top 10 States", _state())
    assert isinstance(patch, RemoveCardPatch)
    assert patch.card_id == "card-top10"


async def test_parse_change_color(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({
        "patch_type": "CHANGE_COLOR",
        "card_id": "card-monthly",
        "color": "#ef4444",
    })

    patch = await intent_parser.parse_instruction("Ubah warna jadi merah", _state())
    assert isinstance(patch, ChangeColorPatch)
    assert patch.color == "#ef4444"


async def test_parse_composite(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({
        "patch_type": "COMPOSITE",
        "patches": [
            {"patch_type": "REMOVE_CARD", "card_id": "card-top10"},
            {"patch_type": "CHANGE_COLOR", "card_id": "card-monthly", "color": "#000000"},
        ],
    })

    patch = await intent_parser.parse_instruction("Hapus top10 dan ubah warna", _state())
    assert isinstance(patch, CompositePatch)
    assert len(patch.patches) == 2


async def test_parse_strips_markdown_fence(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = (
        "```json\n"
        + json.dumps({"patch_type": "REMOVE_CARD", "card_id": "card-top10"})
        + "\n```"
    )

    patch = await intent_parser.parse_instruction("Hapus", _state())
    assert isinstance(patch, RemoveCardPatch)


async def test_parse_invalid_json_retries(mock_generate_chat, mock_cache):
    mock_generate_chat.side_effect = [
        "not a json at all",
        json.dumps({"patch_type": "REMOVE_CARD", "card_id": "card-top10"}),
    ]

    patch = await intent_parser.parse_instruction("Hapus", _state())
    assert isinstance(patch, RemoveCardPatch)
    assert mock_generate_chat.await_count == 2


async def test_parse_invalid_json_twice_raises(mock_generate_chat, mock_cache):
    mock_generate_chat.side_effect = ["bad", "still bad"]

    with pytest.raises(intent_parser.IntentParseError):
        await intent_parser.parse_instruction("Hapus", _state())


async def test_parse_unknown_patch_type_raises(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({"patch_type": "NOT_REAL"})

    with pytest.raises(intent_parser.IntentParseError):
        await intent_parser.parse_instruction("???", _state())


async def test_empty_instruction_raises(mock_cache):
    with pytest.raises(intent_parser.IntentParseError):
        await intent_parser.parse_instruction("", _state())


async def test_cache_hit_skips_llm(mock_generate_chat, mock_cache):
    mock_generate_chat.return_value = json.dumps({
        "patch_type": "REMOVE_CARD", "card_id": "card-top10",
    })
    await intent_parser.parse_instruction("Hapus", _state())
    call_count_1 = mock_generate_chat.await_count

    # Second call — should hit cache
    await intent_parser.parse_instruction("Hapus", _state())
    assert mock_generate_chat.await_count == call_count_1