import pytest
from unittest.mock import AsyncMock, patch

from app.agents import query_generator

@pytest.fixture
def mock_generate_chat():
    """Patch generate_chat inside the query_generator namespace."""
    with patch.object(
        query_generator, "generate_chat", new_callable=AsyncMock
    ) as mock:
        yield mock


SAMPLE_CONTEXT = (
    "table: transactions, column: id (int), date (date), amount (numeric)\n"
    "table: fraud_labels, column: transaction_id (int), fraud_label (text)"
)

async def test_generate_query_plain_sql(mock_generate_chat):
    """LLM returns plain SQL without code fences."""
    sql = "SELECT COUNT(*) FROM transactions WHERE date > '2024-01-01'"
    mock_generate_chat.return_value = sql

    result = await query_generator.generate_query(
        "How many transactions in January?", SAMPLE_CONTEXT
    )

    assert result == sql


async def test_generate_query_with_sql_fence(mock_generate_chat):
    """LLM wraps SQL with ```sql ... ``` → fences stripped."""
    mock_generate_chat.return_value = (
        "```sql\nSELECT * FROM transactions LIMIT 10\n```"
    )

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == "SELECT * FROM transactions LIMIT 10"
    assert "```" not in result


async def test_generate_query_with_plain_fence(mock_generate_chat):
    """LLM wraps SQL with ``` ... ``` (no language tag) → stripped."""
    mock_generate_chat.return_value = "```\nSELECT 1\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == "SELECT 1"


async def test_generate_query_strips_whitespace(mock_generate_chat):
    """Surrounding whitespace is trimmed."""
    mock_generate_chat.return_value = "\n\n   SELECT 1   \n\n"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == "SELECT 1"


async def test_generate_query_multiline_sql(mock_generate_chat):
    """Multi-line SQL is preserved after fence stripping."""
    multiline_sql = (
        "SELECT t.id, t.amount\n"
        "FROM transactions t\n"
        "JOIN fraud_labels f ON f.transaction_id = t.id\n"
        "WHERE f.fraud_label = 'fraud'\n"
        "LIMIT 1000"
    )
    mock_generate_chat.return_value = f"```sql\n{multiline_sql}\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == multiline_sql


async def test_generate_query_calls_generate_chat_correctly(mock_generate_chat):
    """Verify messages, temperature, and argument structure."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query(
        "How many transactions?", SAMPLE_CONTEXT
    )

    mock_generate_chat.assert_awaited_once()
    call_args = mock_generate_chat.call_args
    messages = call_args.args[0]

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == query_generator.QUERY_GEN_SYSTEM_PROMPT
    assert messages[1]["role"] == "user"

    assert call_args.kwargs.get("temperature") == 0.0


async def test_generate_query_includes_metadata_context(mock_generate_chat):
    """metadata_context must appear in the user message."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query(
        "How many transactions?", SAMPLE_CONTEXT
    )

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert SAMPLE_CONTEXT in user_message
    assert "How many transactions?" in user_message
    assert "SQL query:" in user_message


async def test_generate_query_includes_user_prompt(mock_generate_chat):
    """User prompt must appear in the user message."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query(
        "Show me fraud transactions", SAMPLE_CONTEXT
    )

    user_message = mock_generate_chat.call_args.args[0][1]["content"]

    assert "Show me fraud transactions" in user_message


async def test_generate_query_uses_zero_temperature(mock_generate_chat):
    """Query generator must be deterministic."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.0


async def test_generate_query_propagates_exception(mock_generate_chat):
    """If generate_chat raises, generate_query must raise too."""
    mock_generate_chat.side_effect = Exception("LLM down")

    with pytest.raises(Exception, match="LLM down"):
        await query_generator.generate_query("test", SAMPLE_CONTEXT)

async def test_generate_query_empty_string(mock_generate_chat):
    """LLM returns empty string → return empty string."""
    mock_generate_chat.return_value = ""

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == ""


async def test_generate_query_only_whitespace(mock_generate_chat):
    """LLM returns only whitespace → return empty string."""
    mock_generate_chat.return_value = "   \n\n  \t  "

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == ""


async def test_generate_query_empty_metadata_context(mock_generate_chat):
    """Empty metadata_context is allowed, must not error."""
    mock_generate_chat.return_value = "SELECT 1"

    result = await query_generator.generate_query("test", "")

    assert result == "SELECT 1"
    user_message = mock_generate_chat.call_args.args[0][1]["content"]
    assert "Schema context:" in user_message


async def test_generate_query_uppercase_fence_not_fully_stripped(mock_generate_chat):
    """
    Current regex (without IGNORECASE) does NOT strip ```SQL properly.
    The 'SQL' prefix stays in the output.

    This test documents current behavior.
    To also strip uppercase fences, add flags=re.IGNORECASE
    in _extract_sql.
    """
    mock_generate_chat.return_value = "```SQL\nSELECT 1\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)

    assert result == "SQL\nSELECT 1"
    assert "```" not in result