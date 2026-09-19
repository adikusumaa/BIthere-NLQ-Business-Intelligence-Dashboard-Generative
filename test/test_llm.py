"""
Tests for Groq LLM client v2.
Mocks langchain_groq.ChatGroq.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents import llm


@pytest.fixture
def mock_chatgroq():
    with patch.object(llm, "ChatGroq") as mock_cls:
        instance = MagicMock()
        instance.ainvoke = AsyncMock()
        instance.astream = MagicMock()
        mock_cls.return_value = instance
        yield mock_cls, instance


def _make_ai_message(content):
    msg = MagicMock()
    msg.content = content
    return msg


async def _async_iter(items):
    for item in items:
        yield item


def test_get_llm_uses_platform_key(mock_chatgroq):
    mock_cls, _ = mock_chatgroq
    llm.get_llm()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["api_key"]
    assert kwargs["model"] == llm.settings.LLM_MODEL


def test_get_llm_uses_workspace_key(mock_chatgroq):
    mock_cls, _ = mock_chatgroq
    llm.get_llm(api_key="gsk_ws_test")
    assert mock_cls.call_args.kwargs["api_key"] == "gsk_ws_test"


def test_get_llm_raises_without_key(mock_chatgroq, monkeypatch):
    monkeypatch.setattr(llm.settings, "GROQ_API_KEY", None)
    with pytest.raises(ValueError, match="No Groq API key"):
        llm.get_llm()


async def test_generate_chat_returns_content(mock_chatgroq):
    _, instance = mock_chatgroq
    instance.ainvoke.return_value = _make_ai_message("Hello")

    result = await llm.generate_chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello"


async def test_generate_chat_custom_params(mock_chatgroq):
    mock_cls, instance = mock_chatgroq
    instance.ainvoke.return_value = _make_ai_message("x")

    await llm.generate_chat(
        [{"role": "user", "content": "x"}],
        temperature=0.9,
        max_tokens=100,
    )
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["temperature"] == 0.9
    assert kwargs["max_tokens"] == 100


async def test_generate_chat_raises_on_error(mock_chatgroq):
    _, instance = mock_chatgroq
    instance.ainvoke.side_effect = Exception("boom")

    with pytest.raises(Exception, match="boom"):
        await llm.generate_chat([{"role": "user", "content": "x"}])


async def test_generate_chat_passes_workspace_key(mock_chatgroq):
    mock_cls, instance = mock_chatgroq
    instance.ainvoke.return_value = _make_ai_message("x")

    await llm.generate_chat(
        [{"role": "user", "content": "x"}], api_key="gsk_ws"
    )
    assert mock_cls.call_args.kwargs["api_key"] == "gsk_ws"


async def test_stream_chat_yields_tokens(mock_chatgroq):
    _, instance = mock_chatgroq
    chunks = [_make_ai_message("Halo"), _make_ai_message(" dunia")]

    async def fake_stream(*args, **kwargs):
        for c in chunks:
            yield c

    instance.astream.side_effect = fake_stream

    tokens = []
    async for t in llm.stream_chat([{"role": "user", "content": "x"}]):
        tokens.append(t)
    assert tokens == ["Halo", " dunia"]


async def test_stream_chat_skips_empty(mock_chatgroq):
    _, instance = mock_chatgroq
    chunks = [_make_ai_message("A"), _make_ai_message(""), _make_ai_message("B")]

    async def fake_stream(*args, **kwargs):
        for c in chunks:
            yield c

    instance.astream.side_effect = fake_stream

    tokens = [t async for t in llm.stream_chat([{"role": "user", "content": "x"}])]
    assert tokens == ["A", "B"]