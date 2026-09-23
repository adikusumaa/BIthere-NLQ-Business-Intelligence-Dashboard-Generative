"""
Knowledge base endpoints: schema metadata, glossary CRUD, re-ingest.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.logging import logger
from app.rag import ingest_schema as rag_schema
from app.rag import ingest_glossary as rag_glossary
from app.workspace import data_sources as ds_mod
from app.workspace import datasets as datasets_mod
from app.workspace import secrets as secret_store
from app.workspace.secrets import SecretNotFoundError
from app.workspace.context import resolve_workspace
from app.core.progress import start_job, update_job, finish_job, fail_job


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/knowledge-base",
    tags=["Knowledge Base"],
)


class GlossaryCreateRequest(BaseModel):
    term: str
    definition: str
    category: Optional[str] = None
    synonyms: Optional[list[str]] = None


class GlossaryUpdateRequest(BaseModel):
    definition: Optional[str] = None
    category: Optional[str] = None
    synonyms: Optional[list[str]] = None


async def _require_rag_keys(workspace_id: str) -> dict:
    """Ensure Pinecone + Google keys are configured for the workspace."""
    ctx = await resolve_workspace(workspace_id)
    if not ctx.pinecone_key:
        raise HTTPException(status_code=400, detail="Pinecone API key not configured")
    if not ctx.google_key:
        raise HTTPException(status_code=400, detail="Google API key not configured")
    return {
        "pinecone_key": ctx.pinecone_key,
        "google_key": ctx.google_key,
        "redis_prefix": ctx.redis_prefix,
        "namespace": ctx.pinecone_namespace,
    }


# ============ Schema metadata ============

@router.get("/schema")
async def get_workspace_schema(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """Fetch current schema of the workspace's default data source."""
    try:
        connector = await ds_mod.get_workspace_connector(workspace_id)
        await connector.connect()
        try:
            schema = await connector.get_schema()
            return {"dialect": connector.get_dialect(), "schema": schema}
        finally:
            await connector.disconnect()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot load schema: {exc}")


# ============ Glossary ============

@router.get("/glossary")
async def list_glossary(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await rag_glossary.list_terms(workspace_id)
    except rag_glossary.GlossaryStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/glossary", status_code=status.HTTP_201_CREATED)
async def add_glossary_term(
    workspace_id: str,
    body: GlossaryCreateRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        return await rag_glossary.add_term(
            workspace_id=workspace_id,
            term=body.term,
            definition=body.definition,
            category=body.category,
            synonyms=body.synonyms,
            source="manual",
            created_by=user["id"],
        )
    except rag_glossary.GlossaryStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/glossary/{term_id}")
async def update_glossary_term(
    workspace_id: str,
    term_id: str,
    body: GlossaryUpdateRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        return await rag_glossary.update_term(term_id, body.model_dump(exclude_none=True))
    except rag_glossary.GlossaryNotFoundError:
        raise HTTPException(status_code=404, detail="Term not found")
    except rag_glossary.GlossaryStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/glossary/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_glossary_term(
    workspace_id: str,
    term_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await rag_glossary.delete_term(term_id)
    except rag_glossary.GlossaryStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/glossary/upload-csv", status_code=status.HTTP_201_CREATED)
async def upload_glossary_csv(
    workspace_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> dict:
    """Bulk import glossary from CSV: term,definition,category,synonyms."""
    content_bytes = await file.read()
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = content_bytes.decode("latin-1")

    try:
        items = await rag_glossary.ingest_from_csv(
            workspace_id, content, created_by=user["id"]
        )
        return {"imported": len(items)}
    except rag_glossary.GlossaryStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ============ Re-ingest ============

@router.post("/reingest")
async def reingest(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    keys = await _require_rag_keys(workspace_id)

    job_key = f"{workspace_id}:reingest"
    start_job(job_key, label="Rebuild knowledge base")
    update_job(job_key, current=0, total=100, message="Loading schema")

    try:
        connector = await ds_mod.get_workspace_connector(workspace_id)
        await connector.connect()
        try:
            schema = await connector.get_schema()
        finally:
            await connector.disconnect()
    except Exception as exc:
        fail_job(job_key, str(exc))
        raise HTTPException(status_code=400, detail=f"Cannot load schema: {exc}")

    update_job(job_key, current=30, total=100, message="Embedding schema")

    schema_result = await rag_schema.ingest_schema(
        workspace_id=workspace_id,
        schema=schema,
        pinecone_api_key=keys["pinecone_key"],
        pinecone_index=None,
        google_api_key=keys["google_key"],
        redis_prefix=keys["redis_prefix"],
        delete_existing=True,
    )

    update_job(job_key, current=70, total=100, message="Embedding glossary")

    glossary_result = await rag_glossary.ingest_glossary(
        workspace_id=workspace_id,
        pinecone_api_key=keys["pinecone_key"],
        pinecone_index=None,
        google_api_key=keys["google_key"],
        redis_prefix=keys["redis_prefix"],
        delete_existing=True,
    )

    update_job(job_key, current=100, total=100, message="Done")

    result = {
        "schema": schema_result,
        "glossary": glossary_result,
        "namespace": keys["namespace"],
    }
    finish_job(job_key, result)
    return result