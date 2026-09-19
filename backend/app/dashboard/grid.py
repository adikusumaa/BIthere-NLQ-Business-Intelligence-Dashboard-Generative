"""
Grid layout engine for 24-column dashboard layout.
Pure functions — no side effects.
"""

from typing import List, Optional, Tuple

from app.dashboard.state_model import Card, Position


GRID_COLS = 24
MIN_SIZE_X = 2
MIN_SIZE_Y = 2
MAX_SIZE_X = 24
MAX_SIZE_Y = 24


def _overlap(a: Position, b: Position) -> bool:
    """True if two grid rectangles overlap."""
    a_right = a.col + a.size_x
    b_right = b.col + b.size_x
    a_bottom = a.row + a.size_y
    b_bottom = b.row + b.size_y
    return not (
        a.col >= b_right
        or a_right <= b.col
        or a.row >= b_bottom
        or a_bottom <= b.row
    )


def check_overlap(pos_a: Position, pos_b: Position) -> bool:
    """Public alias — True if positions overlap."""
    return _overlap(pos_a, pos_b)


def find_free_position(cards: List[Card], size_x: int, size_y: int) -> Position:
    """
    Find the first free slot on the grid that fits the given size.
    Scans rows top to bottom, columns left to right.
    """
    size_x = max(MIN_SIZE_X, min(MAX_SIZE_X, size_x))
    size_y = max(MIN_SIZE_Y, min(MAX_SIZE_Y, size_y))

    row = 0
    while row < 1000:
        for col in range(0, GRID_COLS - size_x + 1):
            candidate = Position(row=row, col=col, size_x=size_x, size_y=size_y)
            if not any(_overlap(candidate, c.position) for c in cards):
                return candidate
        row += 1
    return Position(row=0, col=0, size_x=size_x, size_y=size_y)


def auto_shift(
    cards: List[Card],
    new_card_position: Position,
) -> List[Tuple[str, Position]]:
    """
    Compute new positions for cards that conflict with new_card_position.
    Shifts them down just enough to clear the new card.

    Returns list of (card_id, new_position).
    """
    shifted: List[Tuple[str, Position]] = []

    current_cards = [c for c in cards]
    for card in current_cards:
        if not _overlap(card.position, new_card_position):
            continue
        new_row = new_card_position.row + new_card_position.size_y
        new_pos = Position(
            row=new_row,
            col=card.position.col,
            size_x=card.position.size_x,
            size_y=card.position.size_y,
        )
        shifted.append((card.id, new_pos))

    return shifted


def reflow(cards: List[Card]) -> List[Tuple[str, Position]]:
    """
    Re-pack cards to remove gaps. Preserves relative order.
    Returns list of (card_id, new_position) only for cards that moved.
    """
    sorted_cards = sorted(cards, key=lambda c: (c.position.row, c.position.col))
    placed: List[Position] = []
    changes: List[Tuple[str, Position]] = []

    row = 0
    col = 0
    row_height = 0

    for card in sorted_cards:
        sx, sy = card.position.size_x, card.position.size_y

        if col + sx > GRID_COLS:
            row += row_height
            col = 0
            row_height = 0

        new_pos = Position(row=row, col=col, size_x=sx, size_y=sy)
        if new_pos != card.position:
            changes.append((card.id, new_pos))

        placed.append(new_pos)
        col += sx
        row_height = max(row_height, sy)

    return changes


def is_valid_position(pos: Position) -> bool:
    """Check bounds."""
    if pos.col < 0 or pos.row < 0:
        return False
    if pos.size_x < MIN_SIZE_X or pos.size_x > MAX_SIZE_X:
        return False
    if pos.size_y < MIN_SIZE_Y or pos.size_y > MAX_SIZE_Y:
        return False
    if pos.col + pos.size_x > GRID_COLS:
        return False
    return True