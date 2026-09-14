"""
Integration test for the chat SSE route.

Requires the backend running on http://localhost:8000 and a valid JWT.
Set TOKEN below, or leave empty to skip auth (if get_current_user is
bypassed in dev).
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
import json

import httpx


BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjkwN2U1YTA0LTc0M2MtNDY2ZS1iMzIyLTg2NTAwNWJhYTEwMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3duYWZhdHd4cXd0bXJtdmx5bnhkLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJmYzAxMDM4ZS1jMjU5LTQ4NTQtOTEzOS02OTRkNGQwYTZlZWUiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzg5MzcyMzc2LCJpYXQiOjE3ODkzNjg3NzYsImVtYWlsIjoiYWRpaWt1c3VtYTEwMDFAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3ODkzNjg3NzZ9XSwic2Vzc2lvbl9pZCI6IjNmMmQzZWZiLWQ5MzctNDYxMC1iYzE0LWE2YmVlZWQyNWJkMyIsImlzX2Fub255bW91cyI6ZmFsc2V9.1tA8dOCds6Y1lzC4SyujNUL1s3SCZdVczjEYNX1Pa3F3SVc0DUGm4gGHfI5whOv9SAVACDyNivaAMSfDGtmT5A"


PROMPT = "Berapa total transaksi fraud di bulan Januari 2010?"


async def main():
    print("=" * 70)
    print("[TEST] POST /api/chat (SSE stream)")
    print("=" * 70)
    print(f"Prompt: {PROMPT}")
    print("=" * 70)

    headers = {"Accept": "text/event-stream"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    payload = {"message": PROMPT}

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", f"{BASE_URL}/api/chat", json=payload, headers=headers
        ) as response:
            print(f"HTTP {response.status_code}")
            if response.status_code != 200:
                body = await response.aread()
                print(body.decode("utf-8", errors="replace"))
                return

            current_event = None
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    raw = line.split(":", 1)[1].strip()
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        data = raw
                    print(f"[{current_event}] {data}")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
