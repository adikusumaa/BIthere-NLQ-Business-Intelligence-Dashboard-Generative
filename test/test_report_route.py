"""
Integration test for the report API route.

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

PAYLOAD = {
    "title": "Fraud Analysis - January 2010",
    "insight": (
        "In January 2010, a total of 15 transactions were flagged as "
        "fraudulent, with a total amount of 1,234.56 USD."
    ),
    "dashboard_url": "http://localhost:3000/public/dashboard/example",
    "channels": ["pdf"],
    "kpis": [
        {"label": "Total Fraud Count", "value": "15"},
        {"label": "Total Fraud Amount (USD)", "value": "1,234.56"},
    ],
}


def _headers() -> dict:
    if not TOKEN:
        raise SystemExit("TOKEN is empty. Paste a fresh Supabase JWT.")
    return {"Authorization": f"Bearer {TOKEN}"}


async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        print("=" * 70)
        print("[TEST 1] POST /api/report - PDF only")
        print("=" * 70)
        response = await client.post(
            f"{BASE_URL}/api/report", json=PAYLOAD, headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:1000])

        print("\n" + "=" * 70)
        print("[TEST 2] POST /api/report - Invalid channel (should 400)")
        print("=" * 70)
        bad = dict(PAYLOAD)
        bad["channels"] = ["telegram"]
        response = await client.post(
            f"{BASE_URL}/api/report", json=bad, headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:400])

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())