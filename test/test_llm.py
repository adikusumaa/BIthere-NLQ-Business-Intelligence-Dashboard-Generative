import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents import llm


# =============================================================
# FIXTURES
# =============================================================

@pytest.fixture
def mock_client():
    """Replace global _client dengan AsyncMock."""
    with patch.object(llm, "_client") as mock:
        yield mock


@pytest.fixture(autouse=True)
def fast_retry(monkeypatch):
    """
    Bikin Tenacity tidak benar-benar sleep saat test.
    Tanpa ini, test retry akan tunggu ~6 detik.
    """
    monkeypatch.setattr(
        "tenacity.nap.time.sleep",
        lambda *args, **kwargs: None,
    )
    try:
        import tenacity.asyncio
        monkeypatch.setattr(
            tenacity.asyncio,
            "sleep",
            AsyncMock(),
        )
    except Exception:
        pass


# =============================================================
# HELPERS
# =============================================================

def _make_response(content):
    """Build fake non-streaming response seperti Groq."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


def _make_chunk(content):
    """Build fake streaming chunk seperti Groq."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = content
    return chunk


async def _async_iter(items):
    """Async iterator dari list."""
    for item in items:
        yield item


# =============================================================
# generate_chat
# =============================================================

async def test_generate_chat(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response("[SUCCESS] Mocked response")
    )

    result = await llm.generate_chat(
        [{"role": "user", "content": "Hello, how are you?"}]
    )

    assert result == "[SUCCESS] Mocked response"
    mock_client.chat.completions.create.assert_awaited_once()

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == llm.MODEL_NAME
    assert kwargs["temperature"] == llm.DEFAULT_TEMPERATURE
    assert kwargs["max_tokens"] == llm.DEFAULT_MAX_TOKENS
    assert kwargs["messages"] == [
        {"role": "user", "content": "Hello, how are you?"}
    ]


async def test_generate_chat_none_content(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response(None)
    )

    result = await llm.generate_chat(
        [{"role": "user", "content": "Hello, how are you?"}]
    )

    assert result == ""


async def test_generate_chat_custom_params(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response("[SUCCESS] Mocked response")
    )

    await llm.generate_chat(
        [{"role": "user", "content": "test"}],
        temperature=0.9,
        max_tokens=100,
    )

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["temperature"] == 0.9
    assert kwargs["max_tokens"] == 100


async def test_generate_chat_retries_on_failure(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("rate limit exceeded")
    )

    with pytest.raises(Exception, match="rate limit exceeded"):
        await llm.generate_chat(
            [{"role": "user", "content": "Hello, how are you?"}]
        )

    assert mock_client.chat.completions.create.await_count == 3


async def test_generate_chat_succeeds_after_retry(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("timeout"),
            Exception("timeout"),
            _make_response("akhirnya berhasil"),
        ]
    )

    result = await llm.generate_chat(
        [{"role": "user", "content": "Halo"}]
    )

    assert result == "akhirnya berhasil"
    assert mock_client.chat.completions.create.await_count == 3


# =============================================================
# stream_chat
# =============================================================

async def test_stream_chat_yields_tokens(mock_client):
    chunks = [
        _make_chunk("Halo"),
        _make_chunk(" "),
        _make_chunk("dunia"),
        _make_chunk("!"),
    ]

    mock_client.chat.completions.create = AsyncMock(
        return_value=_async_iter(chunks)
    )

    tokens = []
    async for token in llm.stream_chat(
        [{"role": "user", "content": "Halo"}]
    ):
        tokens.append(token)

    assert tokens == ["Halo", " ", "dunia", "!"]

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["stream"] is True
    assert kwargs["model"] == llm.MODEL_NAME


async def test_stream_chat_skips_none_tokens(mock_client):
    chunks = [
        _make_chunk("Halo"),
        _make_chunk(None),
        _make_chunk("dunia"),
        _make_chunk(None),
    ]

    mock_client.chat.completions.create = AsyncMock(
        return_value=_async_iter(chunks)
    )

    tokens = [
        t async for t in llm.stream_chat(
            [{"role": "user", "content": "x"}]
        )
    ]

    assert tokens == ["Halo", "dunia"]


async def test_stream_chat_skips_empty_string_tokens(mock_client):
    chunks = [
        _make_chunk("A"),
        _make_chunk(""),
        _make_chunk("B"),
    ]

    mock_client.chat.completions.create = AsyncMock(
        return_value=_async_iter(chunks)
    )

    tokens = [
        t async for t in llm.stream_chat(
            [{"role": "user", "content": "x"}]
        )
    ]

    assert tokens == ["A", "B"]


async def test_stream_chat_raises_on_error(mock_client):
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("stream failed")
    )

    with pytest.raises(Exception, match="stream failed"):
        async for _ in llm.stream_chat(
            [{"role": "user", "content": "x"}]
        ):
            pass


async def test_stream_chat_error_after_partial_tokens(mock_client):
    async def failing_stream():
        yield _make_chunk("Halo")
        yield _make_chunk(" dunia")
        raise Exception("koneksi putus")

    mock_client.chat.completions.create = AsyncMock(
        return_value=failing_stream()
    )

    tokens = []
    with pytest.raises(Exception, match="koneksi putus"):
        async for token in llm.stream_chat(
            [{"role": "user", "content": "x"}]
        ):
            tokens.append(token)

    assert tokens == ["Halo", " dunia"]