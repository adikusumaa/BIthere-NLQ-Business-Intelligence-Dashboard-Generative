"""
Ingest successful NLQ + SQL pairs to improve future retrieval.
Namespace: workspace_{id}/query_history
"""

from typing import Dict, Optional

from app.core.logging import logger
from app.rag.embedding import embed_text
from app.rag.pinecone_client import build_pinecone, workspace_namespace


async def ingest_query_history(
    workspace_id: str,
    prompt: str,
    generated_query: str,
    pinecone_api_key: str,
    pinecone_index: str,
    google_api_key: str,
    redis_prefix: str = "",
    table_hint: Optional[str] = None,
) -> bool:
    """
    Embed a successful (prompt, SQL) pair and store it for future few-shot retrieval.
    """
    namespace = workspace_namespace(workspace_id, "query_history")
    client = build_pinecone(pinecone_api_key, pinecone_index)

    doc_text = f"Question: {prompt}\nSQL: {generated_query}"
    embedding = await embed_text(doc_text, api_key=google_api_key, redis_prefix=redis_prefix)

    import hashlib
    vector_id = "q::" + hashlib.md5(doc_text.encode("utf-8")).hexdigest()

    vector = {
        "id": vector_id,
        "values": embedding,
        "metadata": {
            "prompt": prompt[:500],
            "sql": generated_query[:2000],
            "table_hint": table_hint or "",
            "text": doc_text[:2500],
        },
    }

    ok = client.upsert([vector], namespace)
    if ok:
        logger.info(f"[SUCCESS] Query history ingested into {namespace}")
    return ok


async def retrieve_similar_queries(
    workspace_id: str,
    prompt: str,
    pinecone_api_key: str,
    pinecone_index: str,
    google_api_key: str,
    redis_prefix: str = "",
    top_k: int = 3,
) -> list:
    """Retrieve top-K similar past queries."""
    namespace = workspace_namespace(workspace_id, "query_history")
    client = build_pinecone(pinecone_api_key, pinecone_index)

    embedding = await embed_text(prompt, api_key=google_api_key, redis_prefix=redis_prefix)
    matches = client.query(embedding, namespace, top_k=top_k)
    return [m.get("metadata", {}) for m in matches]