import httpx
from app.core.config import settings
from app.core.logging import log_info, log_error

_client = httpx.AsyncClient(base_url=settings.METABASE_URL, timeout=30.0)
_session_token: str | None = None


async def _authenticate() -> str:
    """Login to Metabase, cache session token."""
    global _session_token
    if _session_token:
        return _session_token

    response = await _client.post(
        "/api/session",
        json={
            "username": settings.METABASE_USERNAME,
            "password": settings.METABASE_PASSWORD,
        },
    )
    response.raise_for_status()
    _session_token = response.json()["id"]
    log_info("Metabase session authenticated")
    return _session_token


async def create_card(name: str, dataset_query: dict, display: str = "table") -> dict:
    """Create a Metabase card (question)."""
    token = await _authenticate()
    response = await _client.post(
        "/api/card",
        headers={"X-Metabase-Session": token},
        json={
            "name": name,
            "dataset_query": dataset_query,
            "display": display,
            "visualization_settings": {},
        },
    )
    response.raise_for_status()
    return response.json()


async def create_dashboard(name: str) -> dict:
    """Create an empty Metabase dashboard."""
    token = await _authenticate()
    response = await _client.post(
        "/api/dashboard",
        headers={"X-Metabase-Session": token},
        json={"name": name},
    )
    response.raise_for_status()
    return response.json()


def get_embed_url(dashboard_id: int) -> str:
    """Build public embed URL for a dashboard."""
    return f"{settings.METABASE_URL}/public/dashboard/{dashboard_id}"