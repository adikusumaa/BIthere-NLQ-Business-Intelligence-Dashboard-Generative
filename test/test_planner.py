import json
import pytest
from unittest.mock import AsyncMock, patch

from app.agents import planner


# =============================================================
# FIXTURES
# =============================================================

@pytest.fixture
def mock_generate_chat():
    """
    Replace planner.generate_chat dengan AsyncMock.
    Planner meng-import generate_chat langsung, jadi kita patch
    di namespace planner, bukan di llm.
    """
    with patch.object(planner, "generate_chat", new_callable=AsyncMock) as mock:
        yield mock


# =============================================================
# HAPPY PATH
# =============================================================

async def test_plan_valid_json(mock_generate_chat):
    """Response JSON valid → dikembalikan apa adanya."""
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

    assert result == expected
    assert result["intent"] == "query_data"
    assert result["needs_dashboard"] is False


async def test_plan_create_dashboard_intent(mock_generate_chat):
    expected = {
        "intent": "create_dashboard",
        "entities": ["transactions"],
        "filters": {},
        "needs_dashboard": True,
        "needs_report": False,
        "reasoning": "User asked for dashboard",
    }
    mock_generate_chat.return_value = json.dumps(expected)

    result = await planner.plan("Buatkan dashboard transaksi")

    assert result["intent"] == "create_dashboard"
    assert result["needs_dashboard"] is True


async def test_plan_send_report_intent(mock_generate_chat):
    expected = {
        "intent": "send_report",
        "entities": [],
        "filters": {},
        "needs_dashboard": False,
        "needs_report": True,
        "reasoning": "User wants report sent",
    }
    mock_generate_chat.return_value = json.dumps(expected)

    result = await planner.plan("Kirim laporan ke Slack")

    assert result["intent"] == "send_report"
    assert result["needs_report"] is True


async def test_plan_combined_intent(mock_generate_chat):
    expected = {
        "intent": "combined",
        "entities": ["transactions"],
        "filters": {},
        "needs_dashboard": True,
        "needs_report": True,
        "reasoning": "User wants dashboard and report",
    }
    mock_generate_chat.return_value = json.dumps(expected)

    result = await planner.plan("Buat dashboard dan kirim ke Slack")

    assert result["intent"] == "combined"
    assert result["needs_dashboard"] is True
    assert result["needs_report"] is True


# =============================================================
# PEMANGGILAN generate_chat
# =============================================================

async def test_plan_calls_generate_chat_with_correct_messages(mock_generate_chat):
    """Cek messages yang dikirim ke LLM dan temperature=0.0."""
    mock_generate_chat.return_value = json.dumps({
        "intent": "query_data",
        "entities": [],
        "filters": {},
        "needs_dashboard": False,
        "needs_report": False,
        "reasoning": "test",
    })

    await planner.plan("Halo")

    mock_generate_chat.assert_awaited_once()
    call_args = mock_generate_chat.call_args
    messages = call_args.args[0]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == planner.PLANNER_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Halo"

    assert call_args.kwargs.get("temperature") == 0.0


async def test_plan_uses_zero_temperature(mock_generate_chat):
    """Planner harus selalu deterministik."""
    mock_generate_chat.return_value = json.dumps({
        "intent": "query_data", "entities": [], "filters": {},
        "needs_dashboard": False, "needs_report": False, "reasoning": "x",
    })

    await planner.plan("test")

    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.0


# =============================================================
# PARSING — edge cases
# =============================================================

async def test_plan_strips_whitespace(mock_generate_chat):
    """Response dengan spasi/newline di sekitar JSON tetap valid."""
    expected = {
        "intent": "query_data", "entities": [], "filters": {},
        "needs_dashboard": False, "needs_report": False, "reasoning": "x",
    }
    mock_generate_chat.return_value = f"\n\n  {json.dumps(expected)}  \n\n"

    result = await planner.plan("test")

    assert result == expected


async def test_plan_invalid_json_returns_fallback(mock_generate_chat):
    """Response bukan JSON → fallback dict dikembalikan."""
    mock_generate_chat.return_value = "This is not JSON at all"

    result = await planner.plan("test")

    assert result["intent"] == "query_data"
    assert result["entities"] == []
    assert result["filters"] == {}
    assert result["needs_dashboard"] is False
    assert result["needs_report"] is False
    assert result["reasoning"] == "fallback due to parse error"


async def test_plan_empty_string_returns_fallback(mock_generate_chat):
    """Response kosong → fallback dict."""
    mock_generate_chat.return_value = ""

    result = await planner.plan("test")

    assert result["intent"] == "query_data"
    assert result["reasoning"] == "fallback due to parse error"


async def test_plan_markdown_wrapped_json_returns_fallback(mock_generate_chat):
    """
    LLM kadang bungkus JSON dengan markdown fence.
    Planner versi ini TIDAK strip fence, jadi harus fallback.
    Test ini mendokumentasikan perilaku saat ini.
    """
    wrapped = '```json\n{"intent": "query_data"}\n```'
    mock_generate_chat.return_value = wrapped

    result = await planner.plan("test")

    assert result["reasoning"] == "fallback due to parse error"


async def test_plan_partial_json_returns_fallback(mock_generate_chat):
    """JSON tidak lengkap → fallback."""
    mock_generate_chat.return_value = '{"intent": "query_data"'

    result = await planner.plan("test")

    assert result["reasoning"] == "fallback due to parse error"


async def test_plan_json_array_returns_fallback(mock_generate_chat):
    """
    LLM return array, bukan object.
    json.loads berhasil, tapi hasilnya list bukan dict.
    Planner harus fallback ke dict default, bukan crash.
    """
    mock_generate_chat.return_value = '[{"intent": "query_data"}]'

    result = await planner.plan("test")

    assert isinstance(result, dict)
    assert result["intent"] == "query_data"
    assert result["entities"] == []
    assert result["needs_dashboard"] is False
    assert result["reasoning"] == "fallback due to non-object JSON"