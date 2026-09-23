"""
Ingest workspace schema metadata into Pinecone namespace workspace_{id}/schema.
Skips per-column embedding for tables with more than 50 columns.
Adds small delay between embed calls to avoid burst rate limits.
"""

import asyncio
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.rag.embedding import embed_text
from app.rag.pinecone_client import build_pinecone, workspace_namespace


LARGE_TABLE_THRESHOLD = 50
INTER_EMBED_DELAY_SECONDS = 0.5


def _schema_docs(schema: Dict[str, Any]) -> List[Dict[str, str]]:
    docs = []
    for table, columns in schema.items():
        col_summary = ", ".join(f"{c['column']} {c['type']}" for c in columns)
        docs.append({
            "id": f"table::{table}",
            "text": f"Table '{table}' has columns: {col_summary}",
            "type": "table",
            "table": table,
        })
        if len(columns) > LARGE_TABLE_THRESHOLD:
            logger.info(
                f"[PROCESS] Table '{table}' has {len(columns)} columns; "
                f"skipping per-column embedding"
            )
            continue
        for col in columns:
            docs.append({
                "id": f"column::{table}::{col['column']}",
                "text": f"Column '{col['column']}' of type {col['type']} in table '{table}'",
                "type": "column",
                "table": table,
                "column": col["column"],
            })
    return docs


async def ingest_schema(
    workspace_id: str,
    schema: Dict[str, Any],
    pinecone_api_key: str,
    pinecone_index: Optional[str],
    google_api_key: str,
    redis_prefix: str = "",
    delete_existing: bool = False,
) -> Dict[str, int]:
    namespace = workspace_namespace(workspace_id, "schema")
    client = build_pinecone(pinecone_api_key, pinecone_index)

    if delete_existing:
        client.delete_namespace(namespace)

    docs = _schema_docs(schema)
    if not docs:
        logger.warning(f"[WARNING] No schema docs to ingest for {workspace_id}")
        return {"tables": 0, "columns": 0, "vectors": 0}

    vectors = []
    total = len(docs)

    for idx, doc in enumerate(docs):
        embedding = await embed_text(
            doc["text"],
            api_key=google_api_key,
            redis_prefix=redis_prefix,
        )
        vectors.append({
            "id": doc["id"],
            "values": embedding,
            "metadata": {
                k: v for k, v in doc.items() if k != "text"
            } | {"text": doc["text"]},
        })

        if idx < total - 1:
            await asyncio.sleep(INTER_EMBED_DELAY_SECONDS)

    client.upsert(vectors, namespace)
    tables = sum(1 for d in docs if d["type"] == "table")
    columns = sum(1 for d in docs if d["type"] == "column")
    logger.info(
        f"[SUCCESS] Ingested {tables} tables, {columns} columns into {namespace}"
    )
    return {"tables": tables, "columns": columns, "vectors": len(vectors)}