"""
Interactive CLI for the BIthere agent graph.

Type a question, press Enter, see the result.
Type 'exit' or 'quit' to stop.

Usage:
    python test/test_graph_e2e.py
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.agents.graph import compile_graph
from app.services.cache import cache


async def ask(app, prompt: str, session_id: str = "cli-001") -> None:
    """Send one prompt to the agent and print the result."""
    print("\n" + "-" * 60)
    state = {"prompt": prompt, "session_id": session_id}
    result = await app.ainvoke(state)

    print(f"\nCache  : {result.get('cache_hit')}")
    print(f"SQL    : {result.get('generated_query')}")
    print(f"Rows   : {len(result.get('query_result', []))}")
    print(f"Insight: {result.get('insight')}")
    if result.get("error"):
        print(f"Error  : {result.get('error')}")
    print("-" * 60)


async def main():
    app = compile_graph()

    print("=" * 60)
    print(" BIthere Interactive CLI")
    print(" Type your question in Indonesian or English.")
    print(" Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    try:
        while True:
            try:
                prompt = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not prompt:
                continue
            if prompt.lower() in {"exit", "quit"}:
                break

            await ask(app, prompt)
    finally:
        await cache.close()
        print("\n[CLEANUP] Redis connection closed")


if __name__ == "__main__":
    asyncio.run(main())