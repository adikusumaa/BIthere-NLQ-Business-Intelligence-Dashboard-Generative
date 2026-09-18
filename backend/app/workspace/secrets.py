"""
Workspace secret vault: CRUD for encrypted API keys per workspace.
All values are encrypted with Fernet before persistence.
"""

from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import settings
from app.core.encryption import vault, EncryptionError
from app.core.logging import logger


SUPPORTED_SERVICES = {
    "groq",
    "google",
    "openai",
    "pinecone",
    "metabase",
    "slack",
    "email",
}


class SecretNotFoundError(Exception):
    """Raised when a requested secret does not exist for a workspace."""


class UnsupportedServiceError(Exception):
    """Raised when an unknown service name is provided."""


class SecretStoreError(Exception):
    """Raised when Supabase operation fails."""


def _headers() -> dict:
    """Standard Supabase REST headers using service role key."""
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(path: str) -> str:
    """Build Supabase REST URL for a given table path."""
    return f"{settings.SUPABASE_URL}/rest/v1/{path}"


def _validate_service(service: str) -> None:
    if service not in SUPPORTED_SERVICES:
        raise UnsupportedServiceError(
            f"Service '{service}' not supported. Allowed: {sorted(SUPPORTED_SERVICES)}"
        )


async def set_secret(
    workspace_id: str,
    service: str,
    value: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Encrypt and upsert a secret for a workspace.
    Overwrites if the (workspace_id, service) pair already exists.
    """
    _validate_service(service)

    encrypted = vault.encrypt(value)
    payload = {
        "workspace_id": workspace_id,
        "service": service,
        "encrypted_value": encrypted.hex(),
        "metadata": metadata or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_secrets"),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            params={"on_conflict": "workspace_id,service"},
            json=payload,
        )

    if response.status_code not in (200, 201):
        logger.error(f"[ERROR] Failed to set secret: {response.status_code} {response.text}")
        raise SecretStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Secret '{service}' stored for workspace {workspace_id}")
    return response.json()[0] if isinstance(response.json(), list) else response.json()


async def get_secret(workspace_id: str, service: str) -> str:
    """
    Retrieve and decrypt a secret. Raises SecretNotFoundError if missing.
    """
    _validate_service(service)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_secrets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "service": f"eq.{service}",
                "select": "encrypted_value",
                "limit": "1",
            },
        )

    if response.status_code != 200:
        raise SecretStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise SecretNotFoundError(f"No secret found for '{service}' in workspace {workspace_id}")

    ciphertext = bytes.fromhex(rows[0]["encrypted_value"])
    return vault.decrypt(ciphertext)


async def get_secret_or_none(workspace_id: str, service: str) -> Optional[str]:
    """Return None instead of raising when secret is missing."""
    try:
        return await get_secret(workspace_id, service)
    except SecretNotFoundError:
        return None


async def list_secrets(workspace_id: str) -> list[dict]:
    """
    List all secrets for a workspace, with masked values (safe for UI).
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_secrets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "id,service,metadata,last_used_at,rotated_at,created_at,updated_at",
            },
        )

    if response.status_code != 200:
        raise SecretStoreError(f"Supabase error {response.status_code}: {response.text}")

    return response.json()


async def rotate_secret(
    workspace_id: str,
    service: str,
    new_value: str,
) -> dict:
    """
    Replace an existing secret with a new value.
    Records rotation timestamp.
    """
    _validate_service(service)

    encrypted = vault.encrypt(new_value)
    now = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(
            _rest_url("workspace_secrets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "service": f"eq.{service}",
            },
            json={
                "encrypted_value": encrypted.hex(),
                "rotated_at": now,
                "updated_at": now,
            },
        )

    if response.status_code != 200:
        raise SecretStoreError(f"Supabase error {response.status_code}: {response.text}")

    rows = response.json()
    if not rows:
        raise SecretNotFoundError(f"Cannot rotate: '{service}' not found in workspace {workspace_id}")

    logger.info(f"[SUCCESS] Secret '{service}' rotated for workspace {workspace_id}")
    return rows[0]


async def delete_secret(workspace_id: str, service: str) -> bool:
    """Delete a secret from the vault."""
    _validate_service(service)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_secrets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "service": f"eq.{service}",
            },
        )

    if response.status_code not in (200, 204):
        raise SecretStoreError(f"Supabase error {response.status_code}: {response.text}")

    logger.info(f"[SUCCESS] Secret '{service}' deleted from workspace {workspace_id}")
    return True


async def touch_secret(workspace_id: str, service: str) -> None:
    """Update last_used_at timestamp without touching the value."""
    now = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.patch(
            _rest_url("workspace_secrets"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "service": f"eq.{service}",
            },
            json={"last_used_at": now},
        )