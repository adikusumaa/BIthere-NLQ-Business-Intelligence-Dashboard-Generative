"""
Integration manager: test connectivity to external services
using a workspace's decrypted API keys.
"""

from typing import Optional

import httpx

from app.core.logging import logger
from app.workspace.secrets import get_secret, SecretNotFoundError


class IntegrationTestError(Exception):
    """Raised when a connection test fails."""


SUPPORTED_INTEGRATIONS = {
    "groq",
    "google",
    "pinecone",
    "metabase",
    "slack",
    "email",
}


async def _test_groq(api_key: str) -> tuple[bool, str]:
    """Ping Groq by listing available models."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
    if response.status_code == 200:
        models = response.json().get("data", [])
        return True, f"OK ({len(models)} models available)"
    return False, f"HTTP {response.status_code}: {response.text[:200]}"


async def _test_google(api_key: str) -> tuple[bool, str]:
    """Ping Google Generative AI by listing models."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
        )
    if response.status_code == 200:
        models = response.json().get("models", [])
        return True, f"OK ({len(models)} models available)"
    return False, f"HTTP {response.status_code}: {response.text[:200]}"


async def _test_pinecone(api_key: str) -> tuple[bool, str]:
    """Ping Pinecone by listing indexes."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://api.pinecone.io/indexes",
            headers={"Api-Key": api_key, "X-Pinecone-API-Version": "2024-07"},
        )
    if response.status_code == 200:
        indexes = response.json().get("indexes", [])
        return True, f"OK ({len(indexes)} indexes)"
    return False, f"HTTP {response.status_code}: {response.text[:200]}"


async def _test_metabase(url: str, username: str, password: str) -> tuple[bool, str]:
    """Ping Metabase by attempting a session token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{url.rstrip('/')}/api/session",
                json={"username": username, "password": password},
            )
    except httpx.RequestError as exc:
        return False, f"Cannot reach Metabase: {exc}"

    if response.status_code == 200:
        return True, "OK (session created)"
    return False, f"HTTP {response.status_code}: {response.text[:200]}"


async def _test_slack(webhook_url: str) -> tuple[bool, str]:
    """Ping Slack webhook with a lightweight message."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json={"text": ":wave: BIthere integration test"},
            )
    except httpx.RequestError as exc:
        return False, f"Cannot reach Slack: {exc}"

    if response.status_code == 200:
        return True, "OK (message delivered)"
    return False, f"HTTP {response.status_code}: {response.text[:200]}"


async def _test_email(resend_key: Optional[str], smtp_user: Optional[str]) -> tuple[bool, str]:
    """Email test: verify Resend key or SMTP creds exist (no email sent)."""
    if resend_key:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {resend_key}"},
            )
        if response.status_code == 200:
            return True, "OK (Resend key valid)"
        return False, f"Resend HTTP {response.status_code}: {response.text[:200]}"
    if smtp_user:
        return True, "OK (SMTP credentials configured)"
    return False, "No Resend key or SMTP user configured"


async def test_integration(
    workspace_id: str,
    service: str,
    extra: Optional[dict] = None,
) -> dict:
    """
    Test a workspace integration by decrypting its stored key
    and pinging the corresponding service.

    Args:
        workspace_id: UUID of the workspace.
        service: one of SUPPORTED_INTEGRATIONS.
        extra: optional dict with additional fields (e.g. metabase url/username).

    Returns:
        dict with keys: service, ok, message, details.
    """
    if service not in SUPPORTED_INTEGRATIONS:
        raise IntegrationTestError(
            f"Service '{service}' not supported. Allowed: {sorted(SUPPORTED_INTEGRATIONS)}"
        )

    try:
        secret = await get_secret(workspace_id, service)
    except SecretNotFoundError:
        return {
            "service": service,
            "ok": False,
            "message": f"No API key configured for '{service}'",
            "details": {},
        }

    extra = extra or {}

    try:
        if service == "groq":
            ok, msg = await _test_groq(secret)
        elif service == "google":
            ok, msg = await _test_google(secret)
        elif service == "pinecone":
            ok, msg = await _test_pinecone(secret)
        elif service == "metabase":
            url = extra.get("url")
            username = extra.get("username")
            if not url or not username:
                return {
                    "service": service,
                    "ok": False,
                    "message": "Metabase test requires 'url' and 'username' in extra",
                    "details": {},
                }
            ok, msg = await _test_metabase(url, username, secret)
        elif service == "slack":
            ok, msg = await _test_slack(secret)
        elif service == "email":
            ok, msg = await _test_email(secret, extra.get("smtp_user"))
        else:
            ok, msg = False, "Unhandled service"
    except Exception as exc:
        logger.error(f"[ERROR] Integration test '{service}' crashed: {exc}")
        return {
            "service": service,
            "ok": False,
            "message": f"Unexpected error: {exc}",
            "details": {},
        }

    logger.info(f"[PROCESS] Integration test '{service}' -> ok={ok}")
    return {
        "service": service,
        "ok": ok,
        "message": msg,
        "details": extra,
    }


async def test_all_integrations(workspace_id: str) -> list[dict]:
    """Run test_integration for every supported service sequentially."""
    results = []
    for service in sorted(SUPPORTED_INTEGRATIONS):
        result = await test_integration(workspace_id, service)
        results.append(result)
    return results