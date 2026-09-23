"""
Schema builder endpoints: DDL generation, apply, rollback.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.workspace import audit
from app.workspace import data_sources as ds_mod
from app.workspace import dataset_parser as parser
from app.workspace import datasets as datasets_mod
from app.workspace.datasets import DatasetNotFoundError, DatasetStoreError
from app.workspace.schema_builder import ddl_generator, executor
from app.workspace.schema_builder.ddl_generator import DDLGenerationError
from app.workspace.schema_builder.executor import ExecutorError
from app.core.progress import start_job, update_job, finish_job, fail_job


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/schema-builder",
    tags=["Schema Builder"],
)


class GenerateDDLRequest(BaseModel):
    dataset_id: str
    table_name: Optional[str] = None
    dialect: Optional[str] = None
    primary_key: Optional[str] = None


class ApplySchemaRequest(BaseModel):
    dataset_id: str
    ddl: str
    columns_resolved: list[dict]
    table_name: str
    drop_if_exists: bool = True
    batch_size: int = 1000


class RollbackRequest(BaseModel):
    dataset_id: str
    table_name: str


@router.post("/generate-ddl")
async def generate_ddl(
    workspace_id: str,
    body: GenerateDDLRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Infer columns from a dataset and produce a CREATE TABLE suggestion."""
    try:
        dataset = await datasets_mod.get_dataset(body.dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        columns = parser.detect_column_types(dataset["file_path"])
        row_count = parser.count_rows(dataset["file_path"])
    except parser.ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    dialect = body.dialect
    if not dialect:
        try:
            connector = await ds_mod.get_workspace_connector(workspace_id)
            dialect = connector.get_dialect()
        except Exception:
            dialect = "duckdb"

    table_name = body.table_name or dataset["name"].rsplit(".", 1)[0].replace(" ", "_").lower()

    try:
        result = ddl_generator.generate_ddl(
            table_name=table_name,
            columns=columns,
            dialect=dialect,
            estimated_rows=row_count,
            primary_key=body.primary_key,
        )
    except DDLGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result["row_count"] = row_count
    return result


@router.post("/apply")
async def apply_schema(
    workspace_id: str,
    body: ApplySchemaRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        dataset = await datasets_mod.get_dataset(body.dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        connector = await ds_mod.get_workspace_connector(workspace_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No data source: {exc}")

    job_key = f"{workspace_id}:apply"
    start_job(job_key, label="Apply schema")

    try:
        await connector.connect()
        update_job(job_key, current=1, total=100, message="Creating table")

        await executor.apply_ddl(
            connector,
            body.ddl,
            drop_if_exists=body.drop_if_exists,
            table_name=body.table_name,
        )

        update_job(job_key, current=5, total=100, message="Inserting data")

        inserted = await executor.bulk_insert(
            connector,
            body.table_name,
            dataset["file_path"],
            body.columns_resolved,
            batch_size=body.batch_size,
            progress_key=job_key,
        )

        schema_record = await datasets_mod.create_schema(
            workspace_id=workspace_id,
            dataset_id=body.dataset_id,
            table_name=body.table_name,
            ddl=body.ddl,
            columns_json=body.columns_resolved,
            status="applied",
        )

        await datasets_mod.update_dataset(
            body.dataset_id,
            {"schema_applied": True, "status": "schema_applied"},
        )

        await audit.log_schema_applied(
            workspace_id, user["id"], schema_record["id"], body.table_name
        )

        finish_job(job_key, {"rows_inserted": inserted, "table_name": body.table_name})

        return {
            "schema_id": schema_record["id"],
            "table_name": body.table_name,
            "rows_inserted": inserted,
        }
    except (ExecutorError, DatasetStoreError) as exc:
        fail_job(job_key, str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await connector.disconnect()


@router.post("/rollback")
async def rollback_schema(
    workspace_id: str,
    body: RollbackRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Drop the table created by an applied schema."""
    try:
        connector = await ds_mod.get_workspace_connector(workspace_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No data source: {exc}")

    try:
        await connector.connect()
        await executor.rollback(connector, body.table_name)

        schema = await datasets_mod.get_schema_for_dataset(body.dataset_id)
        if schema:
            await datasets_mod.update_schema(schema["id"], {"status": "rolled_back"})

        await datasets_mod.update_dataset(
            body.dataset_id,
            {"schema_applied": False, "status": "uploaded"},
        )

        await audit.log_schema_rolled_back(
            workspace_id, user["id"], schema["id"] if schema else "unknown"
        )

        return {"table_name": body.table_name, "rolled_back": True}
    except ExecutorError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await connector.disconnect()


@router.get("/{dataset_id}")
async def get_schema(
    workspace_id: str,
    dataset_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    schema = await datasets_mod.get_schema_for_dataset(dataset_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found for this dataset")
    return schema