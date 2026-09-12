import os
from typing import AsyncGenerator
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import log_info, log_error

_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2048


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)

async def generate_chat(
    messages: list[dict],
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    try:
        response = await _client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        log_error(f"Groq generate_chat failed: {exc}")
        raise


async def stream_chat(
    messages: list[dict],
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> AsyncGenerator[str, None]:
    try:
        stream = await _client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token
    except Exception as exc:
        log_error(f"Groq stream_chat failed: {exc}")
        raise