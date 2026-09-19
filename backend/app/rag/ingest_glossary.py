"""
Glossary CRUD (Postgres) + ingest into Pinecone namespace workspace_{id}/glossary.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.rag.embedding import embed_text
from app.rag.pinecone_client import build_pinecone, workspace_namespace


class GlossaryStoreError(Exception):
    """Raised when a Supabase operation fails."""


class GlossaryNotFoundError(Exception):
    """Raised when a glossary term is not found."""


def _headers() -> dict:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(path: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{path}"


# ============ Postgres CRUD ============

async def add_term(
    workspace_id: str,
    term: str,
    definition: str,
    category: Optional[str] = None,
    synonyms: Optional[List[str]] = None,
    source: str = "manual",
    created_by: Optional[str] = None,
) -> dict:
    if not term or not definition:
        raise GlossaryStoreError("Term and definition are required")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "workspace_id": workspace_id,
        "term": term.strip(),
        "definition": definition.strip(),
        "category": category,
        "synonyms": synonyms or [],
        "source": source,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_glossary"),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "workspace_id,term"},
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise GlossaryStoreError(f"Supabase error {response.status_code}: {response.text}")

    row = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Glossary term added: {term}")
    return row


async def list_terms(workspace_id: str) -> List[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_glossary"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "*",
                "order": "term.asc",
            },
        )
    if response.status_code != 200:
        raise GlossaryStoreError(f"Supabase error {response.status_code}: {response.text}")
    return response.json()


async def get_term(term_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_glossary"),
            headers=_headers(),
            params={"id": f"eq.{term_id}", "select": "*", "limit": "1"},
        )
    if response.status_code != 200:
        raise GlossaryStoreError(f"Supabase error {response.status_code}: {response.text}")
    rows = response.json()
    if not rows:
        raise GlossaryNotFoundError(f"Term {term_id} not found")
    return rows[0]


async def update_term(term_id: str, updates: dict) -> dict:
    allowed = {"definition", "category", "synonyms"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        raise GlossaryStoreError("No valid fields to update")

    filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspace_glossary"),
            headers=_headers(),
            params={"id": f"eq.{term_id}"},
            json=filtered,
        )
    if response.status_code != 200:
        raise GlossaryStoreError(f"Supabase error {response.status_code}: {response.text}")
    rows = response.json()
    if not rows:
        raise GlossaryNotFoundError(f"Term {term_id} not found")
    return rows[0]


async def delete_term(term_id: str) -> bool:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_glossary"),
            headers=_headers(),
            params={"id": f"eq.{term_id}"},
        )
    if response.status_code not in (200, 204):
        raise GlossaryStoreError(f"Supabase error {response.status_code}: {response.text}")
    return True


# ============ CSV import ============

async def ingest_from_csv(
    workspace_id: str,
    csv_content: str,
    created_by: Optional[str] = None,
) -> List[dict]:
    """
    CSV columns: term,definition,category,synonyms (synonyms pipe-separated).
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    results = []
    for row in reader:
        term = (row.get("term") or "").strip()
        definition = (row.get("definition") or "").strip()
        if not term or not definition:
            continue
        synonyms = (row.get("synonyms") or "").strip()
        synonyms_list = [s.strip() for s in synonyms.split("|") if s.strip()]
        results.append(await add_term(
            workspace_id=workspace_id,
            term=term,
            definition=definition,
            category=(row.get("category") or "").strip() or None,
            synonyms=synonyms_list,
            source="csv",
            created_by=created_by,
        ))
    logger.info(f"[SUCCESS] CSV import: {len(results)} terms added")
    return results


# ============ Pinecone ingest ============

async def ingest_glossary(
    workspace_id: str,
    pinecone_api_key: str,
    pinecone_index: str,
    google_api_key: str,
    redis_prefix: str = "",
    delete_existing: bool = False,
) -> Dict[str, int]:
    """Embed all glossary terms for a workspace and upsert to Pinecone."""
    namespace = workspace_namespace(workspace_id, "glossary")
    client = build_pinecone(pinecone_api_key, pinecone_index)

    if delete_existing:
        client.delete_namespace(namespace)

    terms = await list_terms(workspace_id)
    if not terms:
        logger.warning(f"[WARNING] No glossary terms for workspace {workspace_id}")
        return {"terms": 0, "vectors": 0}

    vectors = []
    for t in terms:
        text = f"Term: {t['term']}. Definition: {t['definition']}"
        if t.get("synonyms"):
            text += f". Synonyms: {', '.join(t['synonyms'])}"
        embedding = await embed_text(text, api_key=google_api_key, redis_prefix=redis_prefix)
        vectors.append({
            "id": f"glossary::{t['term'].lower()}",
            "values": embedding,
            "metadata": {
                "term": t["term"],
                "definition": t["definition"],
                "category": t.get("category") or "",
                "text": text,
            },
        })

    client.upsert(vectors, namespace)
    logger.info(f"[SUCCESS] Ingested {len(vectors)} glossary vectors to {namespace}")
    return {"terms": len(terms), "vectors": len(vectors)}