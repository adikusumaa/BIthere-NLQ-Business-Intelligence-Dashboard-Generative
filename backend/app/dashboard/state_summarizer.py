from typing import List

from app.dashboard.state_model import DashboardState


def summarize_state(state: DashboardState) -> str:
    """
    Produce a concise textual summary of the dashboard state for LLM prompts.
    Only emits fields the intent parser needs: page names, card ids/titles/
    types/positions, and filter summaries.
    """
    lines: List[str] = []

    lines.append(
        f"Dashboard version: {state.version}"
        + (f" (parent v{state.parent_version})" if state.parent_version else "")
    )
    lines.append(f"Total pages: {len(state.pages)}")

    for page in state.pages:
        lines.append(f"\nPage '{page.name}' (id={page.id}):")
        if not page.cards:
            lines.append("  (no cards)")
        for card in page.cards:
            pos = card.position
            lines.append(
                f"  - card_id={card.id} | title=\"{card.title}\" | "
                f"type={card.type} | pos=(r{pos.row},c{pos.col},{pos.size_x}x{pos.size_y})"
            )
            if card.style.color:
                lines.append(f"      color={card.style.color}")

        if page.filters:
            lines.append("  filters:")
            for f in page.filters:
                lines.append(
                    f"    - filter_id={f.id} | name=\"{f.name}\" | "
                    f"type={f.type} | column={f.column}"
                )
        else:
            lines.append("  filters: none")

    return "\n".join(lines)