"""
Data source registry: CRUD for workspace data sources
and factory to build a connector instance from a stored source.
"""

from datetime import datetime, timezone
from typing import Optional

import httpx

from app.connectors import build_connector
from app.connectors.base import BaseConnector, ConnectorConfig
from app.core.config import settings
from app.core.encryption import vault
from app.core.logging import logger
from app.workspace.context import invalidate_workspace_context


SUPPORTED_TYPES = {"postgresql", "mysql", "mongodb", "sqlite", "duckdb"}


class DataSourceNotFoundError(Exception):
    """Raised when a data source is not found."""


class DataSourceStoreError(Exception):
    """Raised when Supabase operation fails."""


class UnsupportedDataSourceError(Exception):
    """Raised for unsupported data source type."""


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


def _validate_type(ds_type: str) -> None:
    if ds_type not in SUPPORTED_TYPES:
        raise UnsupportedDataSourceError(
            f"Type '{ds_type}' not supported. Allowed: {sorted(SUPPORTED_TYPES)}"
        )


def _build_connection_payload(
    ds_type: str,
    connection: Optional[str],
    host: Optional[str],
    port: Optional[int],
    database: Optional[str],
    username: Optional[str],
    password: Optional[str],
) -> tuple[Optional[str], dict]:
    """
    Return (encrypted_connection_or_none, config_dict).
    - For SQLite/DuckDB: connection is the file path.
    - For others: either connection_string OR host/port/user/pass/db.
    """
    config: dict = {}

    if ds_type in ("sqlite", "duckdb"):
        if not connection:
            raise DataSourceStoreError(f"{ds_type} requires a file path in 'connection'")
        return vault.encrypt(connection).hex(), config

    if connection:
        return vault.encrypt(connection).hex(), config

    if not (host and database):
        raise DataSourceStoreError("Provide connection_string OR (host + database)")

    config = {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password_encrypted": vault.encrypt(password or "").hex() if password else None,
    }
    return None, config


async def add_data_source(
    workspace_id: str,
    name: str,
    ds_type: str,
    connection: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    is_default: bool = False,
) -> dict:
    """Register a new data source for a workspace."""
    _validate_type(ds_type)

    if not name or not name.strip():
        raise DataSourceStoreError("Data source name is required")

    encrypted_conn, config = _build_connection_payload(
        ds_type, connection, host, port, database, username, password
    )

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "workspace_id": workspace_id,
        "name": name.strip(),
        "type": ds_type,
        "encrypted_connection": encrypted_conn,
        "config": config,
        "is_default": is_default,
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise DataSourceStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )

    row = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Data source added: {row['id']} ({ds_type})")

    if is_default:
        await set_default(workspace_id, row["id"])

    await invalidate_workspace_context(workspace_id)
    return row


async def list_data_sources(workspace_id: str) -> list[dict]:
    """List all data sources for a workspace (without exposing secrets)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "id,name,type,is_default,last_tested_at,last_test_ok,created_at,updated_at",
                "order": "created_at.asc",
            },
        )

    if response.status_code != 200:
        raise DataSourceStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )
    return response.json()


async def get_data_source(ds_id: str) -> dict:
    """Fetch a data source (with encrypted fields)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={"id": f"eq.{ds_id}", "select": "*", "limit": "1"},
        )

    if response.status_code != 200:
        raise DataSourceStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )

    rows = response.json()
    if not rows:
        raise DataSourceNotFoundError(f"Data source {ds_id} not found")
    return rows[0]


async def set_default(workspace_id: str, ds_id: str) -> None:
    """Mark one data source as default and clear others."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.patch(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={"workspace_id": f"eq.{workspace_id}"},
            json={"is_default": False},
        )
        await client.patch(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={"id": f"eq.{ds_id}"},
            json={"is_default": True},
        )

    await invalidate_workspace_context(workspace_id)
    logger.info(f"[SUCCESS] Data source {ds_id} set as default")


async def delete_data_source(ds_id: str) -> bool:
    """Delete a data source."""
    ds = await get_data_source(ds_id)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={"id": f"eq.{ds_id}"},
        )

    if response.status_code not in (200, 204):
        raise DataSourceStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )

    await invalidate_workspace_context(ds["workspace_id"])
    logger.info(f"[SUCCESS] Data source deleted: {ds_id}")
    return True


async def update_test_status(ds_id: str, ok: bool) -> None:
    """Record the result of a connection test."""
    now = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.patch(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={"id": f"eq.{ds_id}"},
            json={"last_tested_at": now, "last_test_ok": ok},
        )


async def test_data_source(ds_id: str) -> tuple[bool, str]:
    """Build a connector and ping the database."""
    ds = await get_data_source(ds_id)

    try:
        connector = _build_connector_from_row(ds)
    except Exception as exc:
        await update_test_status(ds_id, False)
        return False, f"Failed to build connector: {exc}"

    try:
        await connector.connect()
        await connector.disconnect()
        await update_test_status(ds_id, True)
        return True, "Connection OK"
    except Exception as exc:
        await update_test_status(ds_id, False)
        return False, f"Connection failed: {exc}"


async def get_workspace_connector(
    workspace_id: str,
    ds_id: Optional[str] = None,
) -> BaseConnector:
    """
    Return a connector for a workspace, using a specific data source
    or the default one.
    """
    if ds_id:
        ds = await get_data_source(ds_id)
    else:
        ds = await _get_default_data_source(workspace_id)

    return _build_connector_from_row(ds)


async def _get_default_data_source(workspace_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_data_sources"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "is_default": "eq.true",
                "select": "*",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise DataSourceStoreError(
            f"Supabase error {response.status_code}: {response.text}"
        )

    rows = response.json()
    if not rows:
        raise DataSourceNotFoundError(
            f"No default data source for workspace {workspace_id}"
        )
    return rows[0]


def _build_connector_from_row(ds: dict) -> BaseConnector:
    """
    Construct a ConnectorConfig from a stored data source row
    and build the connector.
    """
    ds_type = ds["type"]
    raw_conn: Optional[str] = None
    if ds.get("encrypted_connection"):
        raw_conn = vault.decrypt(bytes.fromhex(ds["encrypted_connection"]))

    cfg = ds.get("config") or {}
    password: Optional[str] = None
    if cfg.get("password_encrypted"):
        password = vault.decrypt(bytes.fromhex(cfg["password_encrypted"]))

    connector_config = ConnectorConfig(
        type=ds_type,
        connection_string=raw_conn,
        host=cfg.get("host"),
        port=cfg.get("port"),
        database=cfg.get("database") or (raw_conn if ds_type in ("sqlite", "duckdb") else None),
        username=cfg.get("username"),
        password=password,
        options={"workspace_id": ds["workspace_id"]},
    )
    return build_connector(connector_config)