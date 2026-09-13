"""
Test for the Dashboard Builder Agent (PRJ 9.1 test_dashboard.py).

Two NLQ scenarios:
1. Single-page dashboard.
2. Multi-page dashboard with tabs.
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import asyncio
from app.agents.dashboard_builder import build_dashboard


SINGLE_PAGE_PROMPT = (
    "Build a fraud analytics dashboard. Show KPI cards for total fraud "
    "count, total fraud amount, average fraud amount, and fraud rate. "
    "Break fraud down by card brand, monthly trend, top 10 states, chip "
    "usage distribution, age group, top 10 cities, and fraud amount by "
    "MCC category. Card Brand, Merchant State, and Merchant City should "
    "be clickable so clicking any bar filters every other chart."
)

MULTI_PAGE_PROMPT = (
    "Build a multi-page fraud analytics dashboard with three pages. "
    "Page 1 'Overview' with KPI cards for total fraud count, total fraud "
    "amount, average amount, fraud rate, plus monthly trend and card "
    "brand breakdown. "
    "Page 2 'Geographic' with top 10 states, top 10 cities, and a state "
    "fraud summary table. "
    "Page 3 'Customer' with fraud by gender, by age group, by credit "
    "score band, and by card type. "
    "Add Card Brand, Merchant State, and Merchant City filters. Card "
    "Brand should be clickable."
)


async def _run_case(prompt: str, label: str):
    print("\n" + "=" * 76)
    print(f"  {label}")
    print("=" * 76)
    print(f"  Prompt: {prompt[:200]}...")
    print("=" * 76)

    result = await build_dashboard(prompt)

    print()
    if result["success"]:
        cfg = result["config"]
        pages = cfg.get("pages", [])
        charts = cfg.get("charts", [])
        total_charts = sum(len(p.get("charts", [])) for p in pages) if pages else len(charts)
        print("[SUCCESS] Dashboard built")
        print(f"  Dashboard ID : {result['dashboard_id']}")
        print(f"  Title        : {cfg.get('title')}")
        print(f"  Pages        : {len(pages)}")
        print(f"  Charts       : {total_charts}")
        print(f"  Filters      : {[f['name'] for f in cfg.get('filters', [])]}")
        print(f"  Embed URL    : {result['embed_url']}")
    else:
        print("[FAILED]")
        print(f"  Error : {result['error']}")


async def main():
    await _run_case(SINGLE_PAGE_PROMPT, "TEST 1 — Single-Page Dashboard")
    await _run_case(MULTI_PAGE_PROMPT, "TEST 2 — Multi-Page Dashboard")


if __name__ == "__main__":
    asyncio.run(main())