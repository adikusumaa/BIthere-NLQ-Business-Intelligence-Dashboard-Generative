"""
Data source registry endpoints (per workspace).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.workspace import audit
from app.workspace import data_sources as ds_mod
from app.workspace.data_sources import (
    DataSourceNotFoundError,
    DataSourceStoreError,
    UnsupportedDataSourceError,
)


router = APIRouter(prefix="/api/workspaces/{workspace_id}/data-sources", tags=["Data Sources"])


class AddDataSourceRequest(BaseModel):
    name: str
    type: str
    connection: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_default: bool = False


class SetDefaultRequest(BaseModel):
    ds_id: str


@router.get("")
async def list_data_sources(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    try:
        return await ds_mod.list_data_sources(workspace_id)
    except DataSourceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_data_source(
    workspace_id: str,
    body: AddDataSourceRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        ds = await ds_mod.add_data_source(
            workspace_id=workspace_id,
            name=body.name,
            ds_type=body.type,
            connection=body.connection,
            host=body.host,
            port=body.port,
            database=body.database,
            username=body.username,
            password=body.password,
            is_default=body.is_default,
        )
        await audit.log_data_source_added(workspace_id, user["id"], ds["id"], body.type)
        return ds
    except UnsupportedDataSourceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except DataSourceStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/set-default")
async def set_default(
    workspace_id: str,
    body: SetDefaultRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        await ds_mod.set_default(workspace_id, body.ds_id)
        return {"ds_id": body.ds_id, "is_default": True}
    except DataSourceNotFoundError:
        raise HTTPException(status_code=404, detail="Data source not found")
    except DataSourceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{ds_id}/test")
async def test_data_source(
    workspace_id: str,
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        ok, message = await ds_mod.test_data_source(ds_id)
        return {"ds_id": ds_id, "ok": ok, "message": message}
    except DataSourceNotFoundError:
        raise HTTPException(status_code=404, detail="Data source not found")


@router.delete("/{ds_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    workspace_id: str,
    ds_id: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await ds_mod.delete_data_source(ds_id)
    except DataSourceNotFoundError:
        raise HTTPException(status_code=404, detail="Data source not found")
    except DataSourceStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))