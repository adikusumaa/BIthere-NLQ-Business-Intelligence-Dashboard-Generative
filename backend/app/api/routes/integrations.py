"""
Integration manager endpoints: set/get/test/delete workspace API keys.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.encryption import vault
from app.core.logging import logger
from app.core.security import get_current_user
from app.workspace import audit
from app.workspace import integrations as integ
from app.workspace import secrets as secret_store
from app.workspace.context import invalidate_workspace_context
from app.workspace.secrets import (
    SecretNotFoundError,
    SecretStoreError,
    UnsupportedServiceError,
)


router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


class SetSecretRequest(BaseModel):
    value: str
    metadata: Optional[dict] = None


class TestIntegrationRequest(BaseModel):
    extra: Optional[dict] = None


@router.get("/{workspace_id}")
async def list_integrations(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    """
    List all secrets for a workspace. Values are NEVER returned;
    only masked previews + metadata.
    """
    try:
        items = await secret_store.list_secrets(workspace_id)
    except SecretStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    services_configured = {item["service"] for item in items}
    result = []
    for service in sorted(secret_store.SUPPORTED_SERVICES):
        configured = service in services_configured
        result.append({
            "service": service,
            "configured": configured,
            "masked_value": "********" if configured else None,
            "last_used_at": next(
                (i.get("last_used_at") for i in items if i["service"] == service), None
            ),
            "rotated_at": next(
                (i.get("rotated_at") for i in items if i["service"] == service), None
            ),
        })
    return result


@router.post("/{workspace_id}/{service}", status_code=status.HTTP_201_CREATED)
async def set_integration(
    workspace_id: str,
    service: str,
    body: SetSecretRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Set or update an API key for a workspace service."""
    try:
        await secret_store.set_secret(
            workspace_id, service, body.value, metadata=body.metadata
        )
        await invalidate_workspace_context(workspace_id)
        await audit.log_api_key_updated(workspace_id, user["id"], service, action="set")
        return {
            "service": service,
            "configured": True,
            "masked_value": vault.mask(body.value),
        }
    except UnsupportedServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SecretStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{workspace_id}/{service}/test")
async def test_integration(
    workspace_id: str,
    service: str,
    body: TestIntegrationRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """Test a workspace integration by pinging the external service."""
    try:
        return await integ.test_integration(
            workspace_id=workspace_id,
            service=service,
            extra=body.extra,
        )
    except integ.IntegrationTestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SecretNotFoundError:
        raise HTTPException(status_code=404, detail=f"No key configured for {service}")


@router.delete("/{workspace_id}/{service}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    workspace_id: str,
    service: str,
    user: dict = Depends(get_current_user),
) -> None:
    try:
        await secret_store.delete_secret(workspace_id, service)
        await invalidate_workspace_context(workspace_id)
        await audit.log_api_key_updated(workspace_id, user["id"], service, action="delete")
    except UnsupportedServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SecretStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{workspace_id}/test-all")
async def test_all(
    workspace_id: str,
    user: dict = Depends(get_current_user),
) -> list[dict]:
    """Run test_integration for every supported service."""
    return await integ.test_all_integrations(workspace_id)