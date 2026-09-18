"""
Audit log service: records all significant workspace actions
(API key changes, dataset uploads, schema apply, role changes, etc.).
"""

from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class AuditStoreError(Exception):
    """Raised when audit log persistence fails."""


def _headers() -> dict:
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _rest_url(path: str) -> str:
    return f"{settings.SUPABASE_URL}/rest/v1/{path}"


async def log_action(
    workspace_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    detail: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Persist a single audit event.
    Failures are logged but never raised to the caller, so the main
    workflow never breaks because audit failed.
    """
    payload = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "detail": detail or {},
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _rest_url("audit_logs"),
                headers=_headers(),
                json=payload,
            )
        if response.status_code not in (200, 201, 204):
            logger.error(
                f"[ERROR] Audit log failed: {response.status_code} {response.text}"
            )
            raise AuditStoreError(
                f"Supabase error {response.status_code}: {response.text}"
            )
        logger.info(f"[SUCCESS] Audit logged: {action} (workspace={workspace_id})")
    except AuditStoreError:
        raise
    except Exception as exc:
        logger.error(f"[ERROR] Audit log unexpected failure: {exc}")


# =====================================================
# Convenience wrappers for common actions
# =====================================================

async def log_workspace_created(workspace_id: str, user_id: str) -> None:
    await log_action(workspace_id, user_id, "workspace.created", "workspace", workspace_id)


async def log_workspace_deleted(workspace_id: str, user_id: str) -> None:
    await log_action(workspace_id, user_id, "workspace.deleted", "workspace", workspace_id)


async def log_member_added(workspace_id: str, actor: str, member_id: str, role: str) -> None:
    await log_action(
        workspace_id, actor, "member.added", "user", member_id,
        detail={"role": role},
    )


async def log_member_role_changed(workspace_id: str, actor: str, member_id: str, new_role: str) -> None:
    await log_action(
        workspace_id, actor, "member.role_changed", "user", member_id,
        detail={"new_role": new_role},
    )


async def log_member_removed(workspace_id: str, actor: str, member_id: str) -> None:
    await log_action(workspace_id, actor, "member.removed", "user", member_id)


async def log_api_key_updated(workspace_id: str, user_id: str, service: str, action: str = "set") -> None:
    await log_action(
        workspace_id, user_id, f"api_key.{action}", "secret", service,
        detail={"service": service},
    )


async def log_dataset_uploaded(workspace_id: str, user_id: str, dataset_id: str, filename: str) -> None:
    await log_action(
        workspace_id, user_id, "dataset.uploaded", "dataset", dataset_id,
        detail={"filename": filename},
    )


async def log_schema_applied(workspace_id: str, user_id: str, schema_id: str, table_name: str) -> None:
    await log_action(
        workspace_id, user_id, "schema.applied", "schema", schema_id,
        detail={"table_name": table_name},
    )


async def log_schema_rolled_back(workspace_id: str, user_id: str, schema_id: str) -> None:
    await log_action(workspace_id, user_id, "schema.rolled_back", "schema", schema_id)


async def log_data_source_added(workspace_id: str, user_id: str, ds_id: str, ds_type: str) -> None:
    await log_action(
        workspace_id, user_id, "data_source.added", "data_source", ds_id,
        detail={"type": ds_type},
    )


async def log_query_executed(workspace_id: str, user_id: str, prompt: str, status: str) -> None:
    await log_action(
        workspace_id, user_id, "query.executed", "query", None,
        detail={"prompt": prompt[:200], "status": status},
    )