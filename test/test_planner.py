"""
Tests for Planner Agent v2.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.agents import planner


@pytest.fixture
def mock_generate_chat():
    with patch.object(planner, "generate_chat", new_callable=AsyncMock) as mock:
        yield mock


async def test_plan_valid_json(mock_generate_chat):
    expected = {
        "intent": "query_data",
        "entities": ["transactions", "fraud_labels"],
        "filters": {"date_range": "2024-01"},
        "needs_dashboard": False,
        "needs_report": False,
        "reasoning": "User wants count of fraud transactions",
    }
    mock_generate_chat.return_value = json.dumps(expected)

    result = await planner.plan("Berapa transaksi fraud bulan lalu?")

    # v2 menambahkan default fields via setdefault
    for k, v in expected.items():
        assert result[k] == v
    assert result["is_in_scope"] is True
    assert result["clarification_needed"] is False
    assert result["report_channel"] == "email"


async def test_plan_create_dashboard_intent(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({
        "intent": "create_dashboard",
        "needs_dashboard": True,
        "needs_report": False,
    })

    result = await planner.plan("Buatkan dashboard transaksi")
    assert result["intent"] == "create_dashboard"
    assert result["needs_dashboard"] is True


async def test_plan_send_report_intent(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({
        "intent": "send_report",
        "needs_report": True,
        "report_channel": "slack",
    })

    result = await planner.plan("Kirim laporan ke Slack")
    assert result["intent"] == "send_report"
    assert result["needs_report"] is True


async def test_plan_out_of_scope(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({
        "is_in_scope": False,
        "clarification_needed": False,
    })

    result = await planner.plan("Siapa presiden Indonesia?")
    assert result["is_in_scope"] is False


async def test_plan_invalid_json_returns_fallback(mock_generate_chat):
    mock_generate_chat.return_value = "not a json {"

    result = await planner.plan("test")
    assert result["is_in_scope"] is False
    assert "parse" in result["reasoning"].lower()


async def test_plan_non_dict_json_returns_fallback(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps(["list", "not", "dict"])

    result = await planner.plan("test")
    assert result["is_in_scope"] is False


async def test_plan_passes_api_key(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({"intent": "query_data"})

    await planner.plan("test", api_key="gsk_ws")
    assert mock_generate_chat.call_args.kwargs["api_key"] == "gsk_ws"


async def test_plan_uses_schema_hint(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({"intent": "query_data"})

    await planner.plan("test", schema_hint="table: users (id, name)")
    system_msg = mock_generate_chat.call_args.args[0][0]["content"]
    assert "users (id, name)" in system_msg


async def test_plan_uses_temperature_zero(mock_generate_chat):
    mock_generate_chat.return_value = json.dumps({"intent": "query_data"})

    await planner.plan("test")
    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.0