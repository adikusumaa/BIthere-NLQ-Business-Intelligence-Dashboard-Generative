"""
Integration tests for audit log service.
"""

import os
import uuid
import pytest

from app.workspace import audit


pytestmark = pytest.mark.skipif(
    not os.getenv("WORKSPACE_ID_TEST"),
    reason="WORKSPACE_ID_TEST not set",
)


@pytest.fixture
def workspace_id() -> str:
    return os.environ["WORKSPACE_ID_TEST"]


async def test_log_action_basic(workspace_id):
    user_id = str(uuid.uuid4())
    await audit.log_action(
        workspace_id=workspace_id,
        user_id=user_id,
        action="test.smoke",
        resource_type="test",
        resource_id="abc",
        detail={"hello": "world"},
    )


async def test_log_workspace_created(workspace_id):
    user_id = str(uuid.uuid4())
    await audit.log_workspace_created(workspace_id, user_id)


async def test_log_api_key_updated(workspace_id):
    user_id = str(uuid.uuid4())
    await audit.log_api_key_updated(workspace_id, user_id, "groq", action="set")
    await audit.log_api_key_updated(workspace_id, user_id, "groq", action="rotate")


async def test_log_dataset_uploaded(workspace_id):
    user_id = str(uuid.uuid4())
    await audit.log_dataset_uploaded(workspace_id, user_id, str(uuid.uuid4()), "sample.csv")


async def test_log_query_executed(workspace_id):
    user_id = str(uuid.uuid4())
    await audit.log_query_executed(
        workspace_id, user_id,
        "Berapa total transaksi fraud bulan lalu?",
        status="success",
    )


async def test_all_wrappers(workspace_id):
    user_id = str(uuid.uuid4())
    member = str(uuid.uuid4())
    ds_id = str(uuid.uuid4())
    schema_id = str(uuid.uuid4())

    await audit.log_member_added(workspace_id, user_id, member, "analyst")
    await audit.log_member_role_changed(workspace_id, user_id, member, "admin")
    await audit.log_member_removed(workspace_id, user_id, member)
    await audit.log_data_source_added(workspace_id, user_id, ds_id, "postgresql")
    await audit.log_schema_applied(workspace_id, user_id, schema_id, "transactions")
    await audit.log_schema_rolled_back(workspace_id, user_id, schema_id)
    await audit.log_workspace_deleted(workspace_id, user_id)