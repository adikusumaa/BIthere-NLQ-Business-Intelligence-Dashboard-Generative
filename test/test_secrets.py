"""
Integration tests for workspace secret vault (hits real Supabase).
Requires WORKSPACE_ID_TEST env variable pointing to a valid workspace UUID.
"""

import os
import pytest

from app.workspace import secrets as secret_store
from app.workspace.secrets import (
    SecretNotFoundError,
    UnsupportedServiceError,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("WORKSPACE_ID_TEST"),
    reason="WORKSPACE_ID_TEST not set; skipping integration tests",
)


@pytest.fixture
def workspace_id() -> str:
    return os.environ["WORKSPACE_ID_TEST"]


@pytest.fixture
def service_name() -> str:
    return "groq"


async def test_set_and_get_secret(workspace_id, service_name):
    await secret_store.delete_secret(workspace_id, service_name)

    original = "gsk_test_value_12345"
    await secret_store.set_secret(workspace_id, service_name, original)

    retrieved = await secret_store.get_secret(workspace_id, service_name)
    assert retrieved == original


async def test_get_secret_raises_when_missing(workspace_id):
    with pytest.raises(SecretNotFoundError):
        await secret_store.get_secret(workspace_id, "openai")


async def test_rotate_secret(workspace_id, service_name):
    await secret_store.set_secret(workspace_id, service_name, "value_old")
    await secret_store.rotate_secret(workspace_id, service_name, "value_new")

    retrieved = await secret_store.get_secret(workspace_id, service_name)
    assert retrieved == "value_new"


async def test_list_secrets(workspace_id, service_name):
    await secret_store.set_secret(workspace_id, service_name, "value_test")

    items = await secret_store.list_secrets(workspace_id)
    services = [item["service"] for item in items]
    assert service_name in services


async def test_delete_secret(workspace_id, service_name):
    await secret_store.set_secret(workspace_id, service_name, "value_to_delete")
    await secret_store.delete_secret(workspace_id, service_name)

    with pytest.raises(SecretNotFoundError):
        await secret_store.get_secret(workspace_id, service_name)


async def test_unsupported_service(workspace_id):
    with pytest.raises(UnsupportedServiceError):
        await secret_store.set_secret(workspace_id, "unknown_service", "x")