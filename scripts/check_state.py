import asyncio
import sys
from app.dashboard import state_store

async def main():
    dashboard_id = sys.argv[1]
    state = await state_store.load_latest(dashboard_id)
    print(f"Dashboard: {state.dashboard_id} v{state.version}")
    print(f"Metabase ID: {state.metabase_dashboard_id}")
    for p in state.pages:
        for c in p.cards:
            print(f"  {c.id} | mb_card={c.metabase.card_id} | mb_dc={c.metabase.dashcard_id} | color={c.style.color} | type={c.type}")

asyncio.run(main())