import json
import pytest
from unittest.mock import AsyncMock, patch

from app.agents import insight_analyzer


# =============================================================
# FIXTURES
# =============================================================

@pytest.fixture
def mock_generate_chat():
    """Patch generate_chat inside the insight_analyzer namespace."""
    with patch.object(
        insight_analyzer, "generate_chat", new_callable=AsyncMock
    ) as mock:
        yield mock


SAMPLE_RESULTS = [
    {"month": "2024-01", "total": 1200},
    {"month": "2024-02", "total": 1500},
    {"month": "2024-03", "total": 1100},
]


# =============================================================
# HAPPY PATH
# =============================================================

async def test_analyze_returns_llm_response(mock_generate_chat):
    """Happy path: returns whatever LLM produces."""
    mock_generate_chat.return_value = "Fraud rose 25% in Feb. Investigate MCC 7995."

    result = await insight_analyzer.analyze(
        "How many fraud transactions last quarter?", SAMPLE_RESULTS
    )

    assert result == "Fraud rose 25% in Feb. Investigate MCC 7995."


async def test_analyze_with_single_result(mock_generate_chat):
    """Single-row results should still work."""
    mock_generate_chat.return_value = "There is one transaction."

    result = await insight_analyzer.analyze(
        "Show me the latest transaction", [{"id": 1}]
    )

    assert result == "There is one transaction."


async def test_analyze_with_empty_results(mock_generate_chat):
    """Empty results list should not crash."""
    mock_generate_chat.return_value = "No data found."

    result = await insight_analyzer.analyze("Any transactions?", [])

    assert result == "No data found."


# =============================================================
# generate_chat INVOCATION
# =============================================================

async def test_analyze_calls_generate_chat_correctly(mock_generate_chat):
    """Verify messages and temperature."""
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test question", SAMPLE_RESULTS)

    mock_generate_chat.assert_awaited_once()
    call_args = mock_generate_chat.call_args
    messages = call_args.args[0]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == insight_analyzer.INSIGHT_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"


async def test_analyze_uses_temperature_0_3(mock_generate_chat):
    """Insight analyzer uses temperature=0.3, not 0.0 or default 0.2."""
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.3


async def test_analyze_user_message_includes_question(mock_generate_chat):
    """User question must appear in the user message."""
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze(
        "How many fraud transactions?", SAMPLE_RESULTS
    )

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert "How many fraud transactions?" in user_message
    assert "User question:" in user_message


async def test_analyze_user_message_includes_row_count(mock_generate_chat):
    """Row count is mentioned in the message."""
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    # 3 rows in SAMPLE_RESULTS
    assert "3 rows" in user_message


async def test_analyze_user_message_includes_results_json(mock_generate_chat):
    """Results JSON should be embedded in the user message."""
    mock_generate_chat.return_value = "insight"

    await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert '"month": "2024-01"' in user_message
    assert '"total": 1200' in user_message


# =============================================================
# TRUNCATION
# =============================================================

async def test_analyze_truncates_to_20_rows(mock_generate_chat):
    """Only first 20 rows should be embedded in the prompt."""
    mock_generate_chat.return_value = "insight"

    # 50 rows
    big_results = [{"id": i} for i in range(50)]

    await insight_analyzer.analyze("test", big_results)

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    # Should include id: 19 (20th row) but not id: 20 (21st row)
    assert '"id": 19' in user_message
    assert '"id": 20' not in user_message
    # Total row count is still 50 (shown in header)
    assert "50 rows" in user_message


async def test_analyze_truncation_with_exactly_20_rows(mock_generate_chat):
    """Exactly 20 rows → all embedded, no truncation."""
    mock_generate_chat.return_value = "insight"

    results = [{"id": i} for i in range(20)]

    await insight_analyzer.analyze("test", results)

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert '"id": 19' in user_message
    assert '"id": 20' not in user_message


async def test_analyze_truncation_with_19_rows(mock_generate_chat):
    """19 rows → all embedded."""
    mock_generate_chat.return_value = "insight"

    results = [{"id": i} for i in range(19)]

    await insight_analyzer.analyze("test", results)

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert '"id": 18' in user_message


# =============================================================
# JSON SERIALIZATION
# =============================================================

async def test_analyze_serializes_non_json_types(mock_generate_chat):
    """
    datetime/Decimal etc. should not crash thanks to default=str.
    """
    import datetime

    mock_generate_chat.return_value = "insight"

    results = [
        {"date": datetime.date(2024, 1, 15), "amount": 100},
    ]

    result = await insight_analyzer.analyze("test", results)

    assert result == "insight"
    user_message = mock_generate_chat.call_args.args[0][1]["content"]
    assert "2024-01-15" in user_message


# =============================================================
# ERROR HANDLING
# =============================================================

async def test_analyze_returns_fallback_on_exception(mock_generate_chat):
    """On LLM failure, return the fallback message (no crash)."""
    mock_generate_chat.side_effect = Exception("LLM down")

    result = await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert result == insight_analyzer.FALLBACK_MESSAGE


async def test_analyze_fallback_message_is_english(mock_generate_chat):
    """Fallback message must be in English."""
    mock_generate_chat.side_effect = Exception("LLM down")

    result = await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert "Sorry" in result
    assert "Maaf" not in result


async def test_analyze_does_not_propagate_exception(mock_generate_chat):
    """Exception must be caught, not raised to caller."""
    mock_generate_chat.side_effect = Exception("boom")

    # Should NOT raise
    result = await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert isinstance(result, str)


async def test_analyze_fallback_on_timeout(mock_generate_chat):
    """Timeout → fallback message."""
    mock_generate_chat.side_effect = TimeoutError("request timed out")

    result = await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert result == insight_analyzer.FALLBACK_MESSAGE


# =============================================================
# RETURN VALUE
# =============================================================

async def test_analyze_returns_string(mock_generate_chat):
    """Return type must always be str."""
    mock_generate_chat.return_value = "some insight"

    result = await insight_analyzer.analyze("test", SAMPLE_RESULTS)

    assert isinstance(result, str)