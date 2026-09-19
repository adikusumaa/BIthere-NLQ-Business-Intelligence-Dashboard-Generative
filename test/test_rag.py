"""
Tests for RAG helpers (no live Pinecone/Google calls in unit tests).
"""

import pytest

from app.rag import ingest_schema, ingest_glossary, ingest_query_history, auto_enrich
from app.rag.pinecone_client import workspace_namespace


# ============ Namespace convention ============

def test_namespace_convention():
    assert workspace_namespace("abc", "schema") == "workspace_abc/schema"
    assert workspace_namespace("abc", "glossary") == "workspace_abc/glossary"
    assert workspace_namespace("abc", "query_history") == "workspace_abc/query_history"


# ============ Schema doc builder ============

def test_schema_docs_builds_table_and_columns():
    schema = {
        "users": [
            {"column": "id", "type": "integer"},
            {"column": "email", "type": "text"},
        ],
        "transactions": [
            {"column": "id", "type": "integer"},
            {"column": "amount", "type": "numeric"},
        ],
    }
    docs = ingest_schema._schema_docs(schema)
    types = [d["type"] for d in docs]
    assert types.count("table") == 2
    assert types.count("column") == 4
    ids = {d["id"] for d in docs}
    assert "table::users" in ids
    assert "column::users::email" in ids


def test_schema_docs_empty():
    assert ingest_schema._schema_docs({}) == []


# ============ Auto-enrich ============

def test_candidate_terms_filters_stopwords():
    prompt = "Berapa total penjualan per kategori bulan lalu untuk fraud?"
    terms = auto_enrich._candidate_terms(prompt)
    assert "penjualan" in terms
    assert "kategori" in terms
    assert "fraud" in terms
    assert "berapa" not in terms
    assert "total" not in terms


def test_candidate_terms_empty_on_stopwords_only():
    terms = auto_enrich._candidate_terms("the a an of for with to")
    assert terms == []


def test_counter_key_format():
    assert auto_enrich._counter_key("ws1", "fraud") == "ws:ws1:term:fraud"


# ============ Integration (live) ============

@pytest.mark.skipif(
    not __import__("os").getenv("RAG_LIVE"),
    reason="Set RAG_LIVE=1 and provide PINECONE/GROQ/GOOGLE keys to run",
)
async def test_ingest_glossary_live():
    import os
    from app.rag import ingest_glossary as ig

    ws_id = os.environ["WORKSPACE_ID_TEST"]
    result = await ig.ingest_glossary(
        workspace_id=ws_id,
        pinecone_api_key=os.environ["PINECONE_API_KEY"],
        pinecone_index=os.environ["PINECONE_INDEX_NAME"],
        google_api_key=os.environ["GOOGLE_API_KEY"],
        redis_prefix=f"ws:{ws_id}:",
        delete_existing=True,
    )
    assert result["vectors"] >= 0