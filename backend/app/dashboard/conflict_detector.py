"""
Conflict detector: optimistic locking via base_version check.
"""

from app.dashboard.state_store import DashboardNotFoundError, load_latest
from app.core.logging import logger


class ConflictError(Exception):
    """Raised when base_version does not match current version."""

    def __init__(self, base_version: int, current_version: int, dashboard_id: str):
        self.base_version = base_version
        self.current_version = current_version
        self.dashboard_id = dashboard_id
        super().__init__(
            f"Dashboard {dashboard_id} has moved to version "
            f"{current_version} (your base: {base_version}). "
            f"Refresh and retry."
        )


async def check_conflict(dashboard_id: str, base_version: int) -> int:
    """
    Verify base_version matches the latest stored version.
    Returns the current version if OK; raises ConflictError otherwise.
    """
    try:
        latest = await load_latest(dashboard_id)
    except DashboardNotFoundError:
        # Fresh dashboard with no versions yet — base must be 0
        if base_version == 0:
            return 0
        raise ConflictError(base_version, 0, dashboard_id)

    if latest.version != base_version:
        raise ConflictError(base_version, latest.version, dashboard_id)

    logger.info(f"[PROCESS] No conflict: dashboard={dashboard_id} v{base_version}")
    return latest.version