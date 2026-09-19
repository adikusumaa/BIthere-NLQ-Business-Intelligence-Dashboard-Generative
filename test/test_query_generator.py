"""
Tests for Query Generator Agent v2.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents import query_generator


@pytest.fixture
def mock_generate_chat():
    with patch.object(
        query_generator, "generate_chat", new_callable=AsyncMock
    ) as mock:
        yield mock


SAMPLE_CONTEXT = (
    "table: transactions, column: id (int), date (date), amount (numeric)\n"
    "table: fraud_labels, column: transaction_id (int), fraud_label (text)"
)


async def test_generate_query_plain_sql(mock_generate_chat):
    sql = "SELECT COUNT(*) FROM transactions WHERE date > '2024-01-01'"
    mock_generate_chat.return_value = sql

    result = await query_generator.generate_query(
        "How many transactions in January?", SAMPLE_CONTEXT
    )
    assert result == sql


async def test_generate_query_with_sql_fence(mock_generate_chat):
    mock_generate_chat.return_value = "```sql\nSELECT * FROM t LIMIT 10\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert result == "SELECT * FROM t LIMIT 10"
    assert "```" not in result


async def test_generate_query_with_plain_fence(mock_generate_chat):
    mock_generate_chat.return_value = "```\nSELECT 1\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert result == "SELECT 1"


async def test_generate_query_strips_whitespace(mock_generate_chat):
    mock_generate_chat.return_value = "\n\n   SELECT 1   \n\n"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert result == "SELECT 1"


async def test_generate_query_multiline_sql(mock_generate_chat):
    multiline = "SELECT t.id\nFROM t\nWHERE x = 1\nLIMIT 1000"
    mock_generate_chat.return_value = f"```sql\n{multiline}\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert result == multiline


async def test_generate_query_includes_metadata_in_system_prompt(mock_generate_chat):
    """v2: metadata_context masuk ke system prompt, bukan user message."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", SAMPLE_CONTEXT)

    system_msg = mock_generate_chat.call_args.args[0][0]["content"]
    assert "transactions" in system_msg
    assert "amount (numeric)" in system_msg


async def test_generate_query_empty_metadata_uses_fallback(mock_generate_chat):
    """v2: metadata kosong → fallback ke FINTECH_SCHEMA_HINT."""
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", "")

    system_msg = mock_generate_chat.call_args.args[0][0]["content"]
    assert "fraud_labels" in system_msg


async def test_generate_query_passes_api_key(mock_generate_chat):
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", SAMPLE_CONTEXT, api_key="gsk_ws")
    assert mock_generate_chat.call_args.kwargs["api_key"] == "gsk_ws"


async def test_generate_query_uses_dialect(mock_generate_chat):
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", SAMPLE_CONTEXT, dialect="sqlite")
    system_msg = mock_generate_chat.call_args.args[0][0]["content"]
    assert "sqlite" in system_msg.lower()


async def test_generate_query_uses_temperature_zero(mock_generate_chat):
    mock_generate_chat.return_value = "SELECT 1"

    await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert mock_generate_chat.call_args.kwargs["temperature"] == 0.0


async def test_generate_query_uppercase_fence_stripped(mock_generate_chat):
    mock_generate_chat.return_value = "```SQL\nSELECT 1\n```"

    result = await query_generator.generate_query("test", SAMPLE_CONTEXT)
    assert result == "SELECT 1"


async def test_generate_query_rejects_placeholder(mock_generate_chat):
    mock_generate_chat.return_value = "SELECT * FROM t WHERE id = $1"

    with pytest.raises(ValueError, match="placeholder"):
        await query_generator.generate_query("test", SAMPLE_CONTEXT)


async def test_generate_query_rejects_curly_placeholder(mock_generate_chat):
    mock_generate_chat.return_value = "SELECT * FROM t WHERE id = {{user_id}}"

    with pytest.raises(ValueError, match="template tag"):
        await query_generator.generate_query("test", SAMPLE_CONTEXT)


async def test_generate_query_llm_failure_propagates(mock_generate_chat):
    mock_generate_chat.side_effect = Exception("LLM down")

    with pytest.raises(Exception, match="LLM down"):
        await query_generator.generate_query("test", SAMPLE_CONTEXT)