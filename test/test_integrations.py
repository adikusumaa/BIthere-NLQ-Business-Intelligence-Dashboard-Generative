"""
Integration tests for workspace integration manager.
Requires WORKSPACE_ID_TEST and at least one secret stored.
"""

import os
import pytest

from app.workspace import integrations as integ
from app.workspace import secrets as secret_store


pytestmark = pytest.mark.skipif(
    not os.getenv("WORKSPACE_ID_TEST"),
    reason="WORKSPACE_ID_TEST not set",
)


@pytest.fixture
def workspace_id() -> str:
    return os.environ["WORKSPACE_ID_TEST"]


async def test_unsupported_service_raises(workspace_id):
    with pytest.raises(integ.IntegrationTestError):
        await integ.test_integration(workspace_id, "unknown_service")


async def test_missing_secret_returns_not_ok(workspace_id):
    await secret_store.delete_secret(workspace_id, "slack")

    result = await integ.test_integration(workspace_id, "slack")
    assert result["service"] == "slack"
    assert result["ok"] is False
    assert "No API key" in result["message"]


async def test_groq_with_invalid_key(workspace_id):
    await secret_store.set_secret(workspace_id, "groq", "gsk_invalid_key_for_test")

    result = await integ.test_integration(workspace_id, "groq")
    assert result["service"] == "groq"
    assert result["ok"] is False
    assert "HTTP" in result["message"] or "error" in result["message"].lower()

    await secret_store.delete_secret(workspace_id, "groq")


async def test_metabase_requires_extra(workspace_id):
    await secret_store.set_secret(workspace_id, "metabase", "dummy")

    result = await integ.test_integration(workspace_id, "metabase")
    assert result["ok"] is False
    assert "url" in result["message"]

    await secret_store.delete_secret(workspace_id, "metabase")


async def test_test_all_integrations_returns_all_services(workspace_id):
    results = await integ.test_all_integrations(workspace_id)
    services = {r["service"] for r in results}
    assert services == integ.SUPPORTED_INTEGRATIONS