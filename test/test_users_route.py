"""
Integration test for admin user management routes.

Requires the backend running and a valid admin JWT.
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

NEW_USER = {
    "email": "test.analyst@example.com",
    "role": "analyst",
    "password": "TestUser2026",
}

def _headers() -> dict:
    if not TOKEN:
        raise SystemExit("TOKEN is empty. Paste a fresh Supabase JWT.")
    return {"Authorization": f"Bearer {TOKEN}"}


async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 70)
        print("[TEST 1] GET /api/users")
        print("=" * 70)
        response = await client.get(
            f"{BASE_URL}/api/users", headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

        print("\n" + "=" * 70)
        print("[TEST 2] POST /api/users (invite)")
        print("=" * 70)
        response = await client.post(
            f"{BASE_URL}/api/users", json=NEW_USER, headers=_headers()
        )
        print(f"HTTP {response.status_code}")
        print(response.text[:800])

        new_user_id = None
        if response.status_code == 201:
            new_user_id = response.json().get("id")

        if new_user_id:
            print("\n" + "=" * 70)
            print("[TEST 3] PUT /api/users/{id} (change role)")
            print("=" * 70)
            response = await client.put(
                f"{BASE_URL}/api/users/{new_user_id}",
                json={"role": "admin"},
                headers=_headers(),
            )
            print(f"HTTP {response.status_code}")
            print(response.text[:800])

            print("\n" + "=" * 70)
            print("[TEST 4] DELETE /api/users/{id}")
            print("=" * 70)
            response = await client.delete(
                f"{BASE_URL}/api/users/{new_user_id}", headers=_headers()
            )
            print(f"HTTP {response.status_code}")
            print(response.text[:800])

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())