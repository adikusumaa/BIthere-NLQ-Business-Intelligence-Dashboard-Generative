from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


VALID_ROLES = {"admin", "analyst", "viewer"}


class InviteError(Exception):
    pass


class InviteNotFoundError(Exception):
    pass


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


async def create_invite(
    workspace_id: str,
    email: str,
    role: str,
    invited_by: Optional[str] = None,
) -> dict:
    email = email.strip().lower()
    if not email or "@" not in email:
        raise InviteError("Valid email is required")
    if role not in VALID_ROLES:
        raise InviteError(f"Role must be one of {sorted(VALID_ROLES)}")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "workspace_id": workspace_id,
        "email": email,
        "role": role,
        "invited_by": invited_by,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _rest_url("workspace_invites"),
            headers={
                **_headers(),
                "Prefer": "resolution=merge-duplicates,return=representation",
            },
            params={"on_conflict": "workspace_id,email"},
            json=payload,
        )

    if response.status_code not in (200, 201):
        raise InviteError(f"Supabase error {response.status_code}: {response.text}")

    row = response.json()[0] if isinstance(response.json(), list) else response.json()
    logger.info(f"[SUCCESS] Invite created: {email} -> workspace {workspace_id} as {role}")
    return row


async def list_invites(workspace_id: str) -> List[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_invites"),
            headers=_headers(),
            params={
                "workspace_id": f"eq.{workspace_id}",
                "select": "*",
                "order": "created_at.desc",
            },
        )
    if response.status_code != 200:
        raise InviteError(f"Supabase error {response.status_code}: {response.text}")
    return response.json()


async def list_pending_for_email(email: str) -> List[dict]:
    email = email.strip().lower()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            _rest_url("workspace_invites"),
            headers=_headers(),
            params={
                "email": f"eq.{email}",
                "status": "eq.pending",
                "select": "*",
            },
        )
    if response.status_code != 200:
        raise InviteError(f"Supabase error {response.status_code}: {response.text}")
    return response.json()


async def mark_accepted(invite_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.patch(
            _rest_url("workspace_invites"),
            headers=_headers(),
            params={"id": f"eq.{invite_id}"},
            json={"status": "accepted", "accepted_at": now, "updated_at": now},
        )


async def revoke_invite(invite_id: str) -> bool:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.delete(
            _rest_url("workspace_invites"),
            headers=_headers(),
            params={"id": f"eq.{invite_id}"},
        )
    if response.status_code not in (200, 204):
        raise InviteError(f"Supabase error {response.status_code}: {response.text}")
    logger.info(f"[SUCCESS] Invite revoked: {invite_id}")
    return True


async def accept_pending_invites_for_user(
    user_id: str,
    email: str,
) -> List[str]:
    from app.workspace import service as ws_service

    invites = await list_pending_for_email(email)
    joined: List[str] = []

    for inv in invites:
        try:
            await ws_service.add_member(
                workspace_id=inv["workspace_id"],
                user_id=user_id,
                role=inv["role"],
                invited_by=inv.get("invited_by"),
            )
            await mark_accepted(inv["id"])
            joined.append(inv["workspace_id"])
            logger.info(
                f"[SUCCESS] Auto-joined workspace {inv['workspace_id']} "
                f"as {inv['role']} for {email}"
            )
        except Exception as exc:
            logger.error(f"[ERROR] Failed to accept invite {inv['id']}: {exc}")

    return joined