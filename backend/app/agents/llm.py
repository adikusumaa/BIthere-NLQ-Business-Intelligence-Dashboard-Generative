"""
Groq LLM client.
Supports per-workspace API key override; falls back to platform key.
"""

from typing import Optional

from langchain_groq import ChatGroq

from app.core.config import settings
from app.core.logging import log_info, log_error


def _resolve_key(api_key: Optional[str]) -> str:
    key = api_key or settings.GROQ_API_KEY
    if not key:
        raise ValueError("No Groq API key available (workspace or platform)")
    return key


def get_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> ChatGroq:
    """Return a ChatGroq client (workspace-scoped if api_key given)."""
    return ChatGroq(
        api_key=_resolve_key(api_key),
        model=model or settings.LLM_MODEL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
    )


async def generate_chat(
    messages: list,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Send messages to Groq and return the assistant text.
    """
    llm = get_llm(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        response = await llm.ainvoke(messages)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        log_error(f"Groq chat failed: {exc}")
        raise


async def stream_chat(
    messages: list,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
):
    """Stream tokens from Groq."""
    llm = get_llm(api_key=api_key, model=model, max_tokens=max_tokens)
    async for chunk in llm.astream(messages):
        text = chunk.content if hasattr(chunk, "content") else str(chunk)
        if text:
            yield text