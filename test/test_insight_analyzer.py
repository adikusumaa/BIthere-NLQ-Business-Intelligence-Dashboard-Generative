"""
Tests for Insight Analyzer v2.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents import insight_analyzer


@pytest.fixture
def mock_generate_chat():
    with patch.object(
        insight_analyzer, "generate_chat", new_callable=AsyncMock
    ) as mock:
        yield mock


SAMPLE_RESULTS = [
    {"month": "2024-01", "total": 1200},
    {"month": "2024-02", "total": 1500},
    {"month": "2024-03", "total": 1100},
]


async def test_analyze_returns_llm_response(mock_generate_chat):
    mock_generate_chat.return_value = "Fraud rose 25% in Feb."

    result = await insight_analyzer.analyze("Q?", SAMPLE_RESULTS)
    assert result == "Fraud rose 25% in Feb."


async def test_analyze_with_single_result(mock_generate_chat):
    mock_generate_chat.return_value = "One transaction."

    result = await insight_analyzer.analyze("Q?", [{"id": 1}])
    assert result == "One transaction."


async def test_analyze_empty_results_does_not_call_llm(mock_generate_chat):
    """v2: empty results → hardcoded fallback, LLM tidak dipanggil."""
    result = await insight_analyzer.analyze("Any?", [])

    assert "No matching data" in result
    mock_generate_chat.assert_not_awaited()


async def test_analyze_calls_generate_chat_correctly(mock_generate_chat):
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test question", SAMPLE_RESULTS)

    mock_generate_chat.assert_awaited_once()
    messages = mock_generate_chat.call_args.args[0]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == insight_analyzer.INSIGHT_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"


async def test_analyze_uses_temperature_0_3(mock_generate_chat):
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test", SAMPLE_RESULTS)
    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.3


async def test_analyze_user_message_includes_question(mock_generate_chat):
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("How many?", SAMPLE_RESULTS)
    user_msg = mock_generate_chat.call_args.args[0][1]["content"]
    assert "How many?" in user_msg


async def test_analyze_user_message_includes_row_count(mock_generate_chat):
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("Q", SAMPLE_RESULTS)
    user_msg = mock_generate_chat.call_args.args[0][1]["content"]
    assert "Total rows returned: 3" in user_msg


async def test_analyze_truncates_to_20_rows(mock_generate_chat):
    mock_generate_chat.return_value = "insight"
    big = [{"id": i} for i in range(50)]

    await insight_analyzer.analyze("Q", big)
    user_msg = mock_generate_chat.call_args.args[0][1]["content"]
    # Hanya 20 row yang dikirim
    assert '"id": 19' in user_msg or '"id": 20' in user_msg
    assert '"id": 25' not in user_msg


async def test_analyze_passes_api_key(mock_generate_chat):
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("Q", SAMPLE_RESULTS, api_key="gsk_ws")
    assert mock_generate_chat.call_args.kwargs["api_key"] == "gsk_ws"


async def test_analyze_fallback_on_exception(mock_generate_chat):
    mock_generate_chat.side_effect = Exception("LLM error")

    result = await insight_analyzer.analyze("Q", SAMPLE_RESULTS)
    assert "Insight generation failed" in result


async def test_analyze_fallback_message_english(mock_generate_chat):
    mock_generate_chat.side_effect = Exception("timeout")

    result = await insight_analyzer.analyze("Q", SAMPLE_RESULTS)
    # fallback pakai kata-kata English
    assert "Retry" in result or "retry" in result.lower()


async def test_analyze_fallback_on_timeout(mock_generate_chat):
    mock_generate_chat.side_effect = TimeoutError("timeout")

    result = await insight_analyzer.analyze("Q", SAMPLE_RESULTS)
    assert "failed" in result.lower() or "Insight" in result