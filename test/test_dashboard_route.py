"""
Integration test for the dashboard API routes.

Requires the backend running on http://localhost:8000 and a valid JWT.
Replace TOKEN with a fresh Supabase access token.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio

import httpx


BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjkwN2U1YTA0LTc0M2MtNDY2ZS1iMzIyLTg2NTAwNWJhYTEwMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3duYWZhdHd4cXd0bXJtdmx5bnhkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJmYzAxMDM4ZS1jMjU5LTQ4NTQtOTEzOS02OTRkNGQwYTZlZWUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzg5MzcyMzc2LCJpYXQiOjE3ODkzNjg3NzYsImVtYWlsIjoiYWRpaWt1c3VtYTEwMDFAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3ODkzNjg3NzZ9XSwic2Vzc2lvbl9pZCI6IjNmMmQzZWZiLWQ5MzctNDYxMC1iYzE0LWE2YmVlZWQyNWJkMyIsImlzX2Fub255bW91cyI6ZmFsc2V9.1tA8dOCds6Y1lzC4SyujNUL1s3SCZdVczjEYNX1Pa3F3SVc0DUGm4gGHfI5whOv9SAVACDyNivaAMSfDGtmT5A"

PROMPT = (
    "Build a fraud analytics dashboard with KPI cards for total fraud "
    "count and total fraud amount, plus charts broken down by card brand, "
    "monthly trend, and top 10 states."
)


def _headers() -> dict:
    if not TOKEN:
        raise SystemExit("TOKEN is empty. Paste a fresh Supabase JWT.")
    return {"Authorization": f"Bearer {TOKEN}"}


async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        print("=" * 70)
        print("[TEST 1] POST /api/dashboard")
        print("=" * 70)
        response = await client.post(
            f"{BASE_URL}/api/dashboard",
            json={"prompt": PROMPT},
            headers=_headers(),
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

        if response.status_code != 200:
            return

        payload = response.json()
        dashboard_id = payload.get("dashboard_id")

        print("\n" + "=" * 70)
        print("[TEST 2] GET /api/dashboard")
        print("=" * 70)
        response = await client.get(
            f"{BASE_URL}/api/dashboard", headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

        print("\n" + "=" * 70)
        print("[TEST 3] GET /api/dashboard/{id}")
        print("=" * 70)
        response = await client.get(
            f"{BASE_URL}/api/dashboard/{dashboard_id}", headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

        print("\n" + "=" * 70)
        print("[TEST 4] DELETE /api/dashboard/{id}")
        print("=" * 70)
        response = await client.delete(
            f"{BASE_URL}/api/dashboard/{dashboard_id}", headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())