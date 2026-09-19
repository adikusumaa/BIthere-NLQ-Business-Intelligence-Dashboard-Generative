"""
End-to-end test for graph_v2: full agent pipeline via workspace context.
Minimal setup: SQLite with a dummy `transactions` table + Groq key.
RAG (Google + Pinecone) is skipped if keys are absent — query_generator
will fall back to the built-in fintech schema hint.

Set TEST_GROQ_KEY to run.
"""

import os
import uuid
import pytest

from app.agents.context import AgentContext
from app.agents.graph_v2 import compile_graph_v2
from app.connectors.base import ConnectorConfig
from app.connectors.sqlite import SQLiteConnector
from app.workspace import secrets as secret_store
from app.workspace import service as ws_service
from app.workspace import data_sources as ds_mod


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_GROQ_KEY"),
    reason="TEST_GROQ_KEY not set; skipping live LLM test",
)


@pytest.fixture
async def workspace_with_sqlite(tmp_path):
    owner = str(uuid.uuid4())
    ws = await ws_service.create_workspace(owner, f"Graph E2E {uuid.uuid4().hex[:6]}")

    # Groq key
    await secret_store.set_secret(ws["id"], "groq", os.environ["TEST_GROQ_KEY"])

    # SQLite file with fintech-like schema
    sqlite_path = tmp_path / "e2e.duckdb"  # actually sqlite file, name is arbitrary
    conn = SQLiteConnector(ConnectorConfig(type="sqlite", connection_string=str(sqlite_path)))
    await conn.connect()
    try:
        await conn.execute_query(
            "CREATE TABLE transactions ("
            "id INTEGER PRIMARY KEY, date TEXT, client_id INTEGER, "
            "card_id INTEGER, amount REAL, mcc INTEGER)"
        )
        await conn.execute_query(
            "INSERT INTO transactions (id, date, client_id, card_id, amount, mcc) VALUES "
            "(1, '2024-01-01', 100, 1, 50.0, 5411),"
            "(2, '2024-01-02', 101, 2, 120.5, 5812),"
            "(3, '2024-01-03', 100, 1, 75.25, 5411)"
        )
    finally:
        await conn.disconnect()

    # Register as workspace data source
    await ds_mod.add_data_source(
        workspace_id=ws["id"],
        name="E2E SQLite",
        ds_type="sqlite",
        connection=str(sqlite_path),
        is_default=True,
    )

    yield ws

    await secret_store.delete_secret(ws["id"], "groq")
    await ws_service.delete_workspace(ws["id"], owner)


async def test_graph_v2_full_pipeline(workspace_with_sqlite):
    ws_id = workspace_with_sqlite["id"]

    # Build connector
    connector = await ds_mod.get_workspace_connector(ws_id)

    # Build minimal AgentContext (no google/pinecone → fallback hint used)
    ctx = AgentContext(
        workspace_id=ws_id,
        redis_prefix=f"ws:{ws_id}:",
        pinecone_namespace=f"workspace_{ws_id}",
        groq_key=os.environ["TEST_GROQ_KEY"],
        google_key=None,
        pinecone_key=None,
        connector=connector,
        dialect="sqlite",
        supports_sql=True,
    )

    graph = compile_graph_v2()
    result = await graph.ainvoke({
        "prompt": "Berapa total amount di tabel transactions?",
        "session_id": "e2e-test",
        "user_email": "test@example.com",
        "context": ctx,
    })

    print("\n=== GRAPH V2 RESULT ===")
    print("plan intent       :", result.get("plan", {}).get("intent"))
    print("generated_query   :", (result.get("generated_query") or "")[:200])
    print("query_result rows :", len(result.get("query_result") or []))
    print("query_result      :", result.get("query_result"))
    print("insight           :", (result.get("insight") or "")[:300])
    print("final_response    :", (result.get("final_response") or "")[:300])
    print("error             :", result.get("error"))
    print("=== END ===\n")

    assert result.get("error") is None, f"Pipeline error: {result.get('error')}"
    assert result.get("generated_query"), "No SQL generated"
    assert result.get("query_result") is not None, "No query result"
    assert result.get("final_response"), "No final response"