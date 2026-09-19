"""
Seed a test dashboard for F-13 editor testing.
Creates one dashboard_versions record with a starter state.
Usage:
    python scripts/seed_test_dashboard.py
Env:
    Requires SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (dari .env)
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add backend to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.dashboard.state_model import (  # noqa: E402
    Card,
    CardStyle,
    DashboardState,
    Page,
    Position,
)
from app.dashboard import state_store  # noqa: E402
from app.workspace import service as ws_service  # noqa: E402


async def main():
    # Find first workspace
    print("[PROCESS] Looking up workspaces...")

    # Get workspaces via REST
    import httpx
    from app.core.config import settings

    key = settings.SUPABASE_SERVICE_ROLE_KEY
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/workspaces"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            url,
            headers=headers,
            params={"select": "id,name,owner_id", "limit": "1"},
        )
    if resp.status_code != 200 or not resp.json():
        print("[ERROR] No workspace found. Create one via the UI first.")
        sys.exit(1)

    ws = resp.json()[0]
    workspace_id = ws["id"]
    print(f"[INFO] Using workspace: {ws['name']} ({workspace_id})")

    # Build a starter state
    dashboard_id = str(uuid.uuid4())
    state = DashboardState(
        dashboard_id=dashboard_id,
        workspace_id=workspace_id,
        version=1,
        pages=[
            Page(
                id="page-1",
                name="Overview",
                cards=[
                    Card(
                        id="card-total",
                        title="Total Amount",
                        type="scalar",
                        sql="SELECT SUM(amount) AS total FROM test_data",
                        position=Position(row=0, col=0, size_x=6, size_y=3),
                    ),
                    Card(
                        id="card-by-city",
                        title="Amount by City",
                        type="bar",
                        sql="SELECT merchant_city, SUM(amount) AS total FROM test_data GROUP BY merchant_city ORDER BY total DESC",
                        position=Position(row=0, col=6, size_x=18, size_y=3),
                        style=CardStyle(color="#3b82f6"),
                    ),
                ],
            ),
        ],
    )

    await state_store.save_version(
        dashboard_id=dashboard_id,
        state=state,
        patch=None,
        user_id=ws["owner_id"],
    )

    print(f"[SUCCESS] Dashboard seeded")
    print(f"[INFO] dashboard_id = {dashboard_id}")
    print(f"[INFO] Open: http://localhost:5173/dashboard/{dashboard_id}/edit")


if __name__ == "__main__":
    asyncio.run(main())