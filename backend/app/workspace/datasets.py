"""
Dataset catalog: CRUD for workspace_datasets + workspace_schemas.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class DatasetNotFoundError(Exception):
    """Raised when a dataset is not found."""


class DatasetStoreError(Exception):
    """Raised when Supabase operation fails."""


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


async def create_dataset(
    workspace_id: str,
    name: str,
    source_type: str,
    file_path: str,
    file_size_bytes: Optional[int] = None,
    row_count: Optional[int] = None,
    column_count: Optional[int] = None,
    target: str = "duckdb",
    created_by: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> dict:
    """Insert a new dataset record."""
    if source_type not in ("csv", "excel", "parquet"):
        raise DatasetStoreError(f"Invalid source_type: {source_type}")
    if target not in ("duckdb", "supabase"):
        raise DatasetStoreError(f"Invalid target: {target}")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "workspace_id": workspace_id,
        "name": name,
        "source_type": source_type,
        "file_path": file_path,
        "file_size_bytes": file_size_bytes,
        "row_count": row_count,
        "column_count": column_count,
        "target": target,
        "status": "uploaded",
        "schema_applied": False,
        "created_by": created_by,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_datasets"),
            headers=_headers(),
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    row = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Dataset created: {row['id']}")
    return row


async def list_datasets(workspace_id: str) -> List[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_datasets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "*",
                "order": "created_at.desc",
            },
        )

    if response.status_code != 200:
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")
    return response.json()


async def get_dataset(dataset_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_datasets"),
            headers=_headers(),
            params={"id": f"eq.{dataset_id}", "select": "*", "limit": "1"},
        )

    if response.status_code != 200:
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
    return rows[0]


async def update_dataset(dataset_id: str, updates: dict) -> dict:
    allowed = {"name", "status", "schema_applied", "target", "metadata",
               "row_count", "column_count", "file_size_bytes"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        raise DatasetStoreError("No valid fields to update")

    filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspace_datasets"),
            headers=_headers(),
            params={"id": f"eq.{dataset_id}"},
            json=filtered,
        )

    if response.status_code != 200:
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
    return rows[0]


async def delete_dataset(dataset_id: str) -> bool:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_datasets"),
            headers=_headers(),
            params={"id": f"eq.{dataset_id}"},
        )

    if response.status_code not in (200, 204):
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Dataset deleted: {dataset_id}")
    return True


# =====================================================
# Workspace schemas
# =====================================================

async def create_schema(
    workspace_id: str,
    dataset_id: str,
    table_name: str,
    ddl: str,
    columns_json: List[dict],
    indexes_json: Optional[List[dict]] = None,
    partitions_json: Optional[List[dict]] = None,
    status: str = "draft",
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "workspace_id": workspace_id,
        "dataset_id": dataset_id,
        "table_name": table_name,
        "ddl": ddl,
        "columns_json": columns_json,
        "indexes_json": indexes_json or [],
        "partitions_json": partitions_json or [],
        "status": status,
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_schemas"),
            headers=_headers(),
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    row = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Schema draft created: {row['id']}")
    return row


async def get_schema_for_dataset(dataset_id: str) -> Optional[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_schemas"),
            headers=_headers(),
            params={
                "dataset_id": f"eq.{dataset_id}",
                "select": "*",
                "order": "created_at.desc",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    return rows[0] if rows else None


async def update_schema(schema_id: str, updates: dict) -> dict:
    allowed = {"ddl", "columns_json", "indexes_json", "partitions_json",
               "status", "applied_at"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        raise DatasetStoreError("No valid fields to update")

    filtered["updated_at"] = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspace_schemas"),
            headers=_headers(),
            params={"id": f"eq.{schema_id}"},
            json=filtered,
        )

    if response.status_code != 200:
        raise DatasetStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise DatasetNotFoundError(f"Schema {schema_id} not found")
    return rows[0]