"""
Test for the Dashboard Builder Agent (PRJ 9.1 test_dashboard.py).

The agent accepts a natural-language dashboard request, generates the
full configuration via the LLM, and renders it in Metabase.

Usage:
    python test/test_dashboard.py
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.agents.dashboard_builder import build_dashboard


NLQ_PROMPT = (
    "Buat dashboard fraud analytics. Tampilkan KPI total fraud count, "
    "total fraud amount, average amount, dan fraud rate. Pecah fraud per "
    "card brand, tren bulanan, top 10 states, distribusi chip usage, age "
    "group, top 10 cities, dan fraud amount per MCC category. Saya ingin "
    "bisa klik salah satu brand, state, atau city dan semua chart "
    "menyesuaikan secara otomatis."
)


async def main():
    print("=" * 76)
    print("  Dashboard Builder Agent - NLQ Test")
    print("=" * 76)
    print(f"  Prompt: {NLQ_PROMPT}")
    print("=" * 76)

    result = await build_dashboard(NLQ_PROMPT)

    print()
    if result["success"]:
        cfg = result["config"]
        print("[SUCCESS] Dashboard built")
        print(f"  Dashboard ID : {result['dashboard_id']}")
        print(f"  Title        : {cfg.get('title')}")
        print(f"  Charts       : {len(cfg.get('charts', []))}")
        print(f"  Filters      : {[f['name'] for f in cfg.get('filters', [])]}")
        print(f"  Embed URL    : {result['embed_url']}")
        print()
        print("=" * 76)
        print("  Open in browser:")
        print(f"  {result['embed_url']}")
        print("=" * 76)
    else:
        print("[FAILED]")
        print(f"  Error : {result['error']}")
        print("=" * 76)


if __name__ == "__main__":
    asyncio.run(main())