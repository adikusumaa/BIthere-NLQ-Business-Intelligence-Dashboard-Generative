"""
Dashboard State Model for F-13.
Represents a dashboard as a JSON tree with pages, cards, filters.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


CardType = Literal["scalar", "bar", "line", "pie", "area", "table", "text"]
FilterType = Literal["category", "date", "number", "text"]


class Position(BaseModel):
    """Grid position in a 24-column layout."""
    row: int = Field(ge=0, default=0)
    col: int = Field(ge=0, le=23, default=0)
    size_x: int = Field(ge=2, le=24, default=6)
    size_y: int = Field(ge=2, le=24, default=3)


class CardStyle(BaseModel):
    color: Optional[str] = None  # hex like "#3b82f6"
    show_legend: bool = False
    number_format: Optional[str] = None  # "comma", "percent", "currency"
    title_size: Optional[int] = None


class MetabaseRef(BaseModel):
    """Reference to the underlying Metabase entities."""
    card_id: Optional[int] = None
    dashcard_id: Optional[int] = None


class Card(BaseModel):
    """A single chart/scalar/text block."""
    id: str
    title: str
    type: CardType
    sql: Optional[str] = None
    position: Position = Field(default_factory=Position)
    style: CardStyle = Field(default_factory=CardStyle)
    metabase: MetabaseRef = Field(default_factory=MetabaseRef)
    filters_applied: List[str] = Field(default_factory=list)


class DashboardFilter(BaseModel):
    """A filter shown on the page, bound to a column."""
    id: str
    name: str
    type: FilterType
    column: str  # "table.column"
    default: Optional[Any] = None
    metabase_parameter_id: Optional[str] = None


class Page(BaseModel):
    """A dashboard page/tab."""
    id: str
    name: str
    layout_columns: int = 24
    cards: List[Card] = Field(default_factory=list)
    filters: List[DashboardFilter] = Field(default_factory=list)


class DashboardMeta(BaseModel):
    """Metadata about how the state was generated."""
    generated_by: Optional[str] = None
    generated_at: Optional[str] = None
    llm_tokens_used: Optional[int] = None


class DashboardState(BaseModel):
    """Full state tree for a dashboard."""
    dashboard_id: str
    workspace_id: str
    metabase_dashboard_id: Optional[int] = None
    version: int = 1
    parent_version: Optional[int] = None
    created_at: Optional[str] = None
    pages: List[Page] = Field(default_factory=list)
    metadata: DashboardMeta = Field(default_factory=DashboardMeta)


# =====================================================
# Helpers
# =====================================================

def find_card(state: DashboardState, card_id: str) -> Optional[Card]:
    """Find a card by id across all pages."""
    for page in state.pages:
        for card in page.cards:
            if card.id == card_id:
                return card
    return None


def find_page_of_card(state: DashboardState, card_id: str) -> Optional[Page]:
    """Return the page containing the card, or None."""
    for page in state.pages:
        for card in page.cards:
            if card.id == card_id:
                return page
    return None


def find_filter(state: DashboardState, filter_id: str) -> Optional[DashboardFilter]:
    """Find a filter by id across all pages."""
    for page in state.pages:
        for f in page.filters:
            if f.id == filter_id:
                return f
    return None


def find_page_of_filter(state: DashboardState, filter_id: str) -> Optional[Page]:
    for page in state.pages:
        for f in page.filters:
            if f.id == filter_id:
                return page
    return None


def find_page(state: DashboardState, page_id: str) -> Optional[Page]:
    for page in state.pages:
        if page.id == page_id:
            return page
    return None


def all_card_ids(state: DashboardState) -> List[str]:
    ids = []
    for page in state.pages:
        for card in page.cards:
            ids.append(card.id)
    return ids