"""
Dataset management endpoints (upload, list, preview, delete).
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.workspace import audit
from app.workspace import dataset_parser as parser
from app.workspace import datasets as ds_mod
from app.workspace import upload as upload_mod
from app.workspace.datasets import DatasetNotFoundError, DatasetStoreError
from app.workspace.upload import UploadError


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/datasets",
    tags=["Datasets"],
)


class UploadResponse(BaseModel):
    dataset_id: str
    name: str
    source_type: str
    row_count: int
    column_count: int
    columns: list[dict]
    preview: dict


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    workspace_id: str,
    file: UploadFile = File(...),
    name: Optional[str] = Form(default=None),
    target: str = Form(default="duckdb"),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Upload a CSV/Excel/Parquet file, parse it, and register a dataset record.
    """
    try:
        saved = await upload_mod.save_upload(workspace_id, file)
    except UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        columns = parser.detect_column_types(saved["stored_path"])
        row_count = parser.count_rows(saved["stored_path"])
        preview = parser.preview(saved["stored_path"], n=100)
    except parser.ParseError as exc:
        upload_mod.delete_upload(saved["stored_path"])
        raise HTTPException(status_code=400, detail=f"Parse failed: {exc}")

    source_type = "csv" if saved["extension"] == ".csv" else (
        "excel" if saved["extension"] in (".xlsx", ".xls") else "parquet"
    )

    try:
        dataset = await ds_mod.create_dataset(
            workspace_id=workspace_id,
            name=name or saved["original_filename"],
            source_type=source_type,
            file_path=saved["stored_path"],
            file_size_bytes=saved["size_bytes"],
            row_count=row_count,
            column_count=len(columns),
            target=target,
            created_by=user["id"],
            metadata={"original_filename": saved["original_filename"]},
        )
        await audit.log_dataset_uploaded(
            workspace_id, user["id"], dataset["id"], saved["original_filename"]
        )
    except DatasetStoreError as exc:
        upload_mod.delete_upload(saved["stored_path"])
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "dataset_id": dataset["id"],
        "name": dataset["name"],
        "source_type": dataset["source_type"],
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "preview": preview,
    }


@router.get("")
async def list_datasets(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await ds_mod.list_datasets(workspace_id)
    except DatasetStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dataset_id}")
async def get_dataset(
    workspace_id: str,
    dataset_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        return await ds_mod.get_dataset(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except DatasetStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    workspace_id: str,
    dataset_id: str,
    n: int = 100,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        dataset = await ds_mod.get_dataset(dataset_id)
        return parser.preview(dataset["file_path"], n=n)
    except DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except parser.ParseError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    workspace_id: str,
    dataset_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        dataset = await ds_mod.get_dataset(dataset_id)
        upload_mod.delete_upload(dataset["file_path"])
        await ds_mod.delete_dataset(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except DatasetStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))