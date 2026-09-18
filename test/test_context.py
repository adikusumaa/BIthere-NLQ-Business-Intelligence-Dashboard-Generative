"""
Integration tests for workspace context resolution (with Redis cache).
"""

import os
import uuid
import pytest

from app.workspace import context as ctx_mod
from app.workspace import service as ws_service
from app.workspace import secrets as secret_store


pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MODE") != "live",
    reason="Integration tests require TEST_MODE=live",
)


@pytest.fixture
async def workspace():
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"Context Test {uuid.uuid4().hex[:6]}")
    await secret_store.set_secret(ws["id"], "groq", "gsk_fake_for_context_test")
    yield ws
    await secret_store.delete_secret(ws["id"], "groq")
    await ws_service.delete_workspace(ws["id"], owner)


async def test_resolve_returns_context(workspace):
    ctx = await ctx_mod.resolve_workspace(workspace["id"])

    assert ctx.workspace_id == workspace["id"]
    assert ctx.workspace_name == workspace["name"]
    assert ctx.owner_id == workspace["owner_id"]
    assert ctx.groq_key == "gsk_fake_for_context_test"
    assert ctx.pinecone_namespace == f"workspace_{workspace['id']}"
    assert ctx.redis_prefix.endswith(":")


async def test_resolve_caches_to_redis(workspace):
    ctx1 = await ctx_mod.resolve_workspace(workspace["id"])
    ctx2 = await ctx_mod.resolve_workspace(workspace["id"])

    assert ctx1.model_dump() == ctx2.model_dump()


async def test_invalidate_removes_cache(workspace):
    await ctx_mod.resolve_workspace(workspace["id"])
    await ctx_mod.invalidate_workspace_context(workspace["id"])

    cached = await ctx_mod._get_redis().get(ctx_mod._redis_key(workspace["id"]))
    assert cached is None


async def test_context_reflects_new_secret(workspace):
    await secret_store.set_secret(workspace["id"], "slack", "https://hooks.slack.com/fake")
    await ctx_mod.invalidate_workspace_context(workspace["id"])

    ctx = await ctx_mod.resolve_workspace(workspace["id"])
    assert ctx.slack_webhook == "https://hooks.slack.com/fake"

    await secret_store.delete_secret(workspace["id"], "slack")