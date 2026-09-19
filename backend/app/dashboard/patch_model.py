"""
Patch Model for F-13.
Discriminated union of 13 patch types + composite wrapper.
"""

from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

from app.dashboard.state_model import (
    Card,
    CardStyle,
    DashboardFilter,
    Position,
)


# =====================================================
# Individual Patch Types
# =====================================================

class AddCardPatch(BaseModel):
    """Add a new card, optionally relative to an existing one."""
    patch_type: Literal["ADD_CARD"] = "ADD_CARD"
    page_id: str
    card: Card
    insert_before: Optional[str] = None  # card_id
    insert_after: Optional[str] = None   # card_id


class RemoveCardPatch(BaseModel):
    patch_type: Literal["REMOVE_CARD"] = "REMOVE_CARD"
    card_id: str


class MoveCardPatch(BaseModel):
    patch_type: Literal["MOVE_CARD"] = "MOVE_CARD"
    card_id: str
    new_position: Position


class SwapCardsPatch(BaseModel):
    patch_type: Literal["SWAP_CARDS"] = "SWAP_CARDS"
    card_id_a: str
    card_id_b: str


class ResizeCardPatch(BaseModel):
    patch_type: Literal["RESIZE_CARD"] = "RESIZE_CARD"
    card_id: str
    new_size: Position


class ChangeColorPatch(BaseModel):
    patch_type: Literal["CHANGE_COLOR"] = "CHANGE_COLOR"
    card_id: str
    color: str  # hex


class ChangeTitlePatch(BaseModel):
    patch_type: Literal["CHANGE_TITLE"] = "CHANGE_TITLE"
    card_id: str
    new_title: str


class ChangeChartTypePatch(BaseModel):
    patch_type: Literal["CHANGE_CHART_TYPE"] = "CHANGE_CHART_TYPE"
    card_id: str
    new_type: str


class UpdateSqlPatch(BaseModel):
    patch_type: Literal["UPDATE_SQL"] = "UPDATE_SQL"
    card_id: str
    new_sql: str


class AddFilterPatch(BaseModel):
    patch_type: Literal["ADD_FILTER"] = "ADD_FILTER"
    page_id: str
    filter: DashboardFilter
    apply_to: Union[List[str], Literal["all"]] = "all"


class RemoveFilterPatch(BaseModel):
    patch_type: Literal["REMOVE_FILTER"] = "REMOVE_FILTER"
    filter_id: str


class RollbackToVersionPatch(BaseModel):
    patch_type: Literal["ROLLBACK_TO_VERSION"] = "ROLLBACK_TO_VERSION"
    target_version: int


# =====================================================
# Composite (recursive)
# =====================================================

class CompositePatch(BaseModel):
    patch_type: Literal["COMPOSITE"] = "COMPOSITE"
    patches: List[Any] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_nested_composite(self):
        for p in self.patches:
            if isinstance(p, CompositePatch) or (
                isinstance(p, dict) and p.get("patch_type") == "COMPOSITE"
            ):
                raise ValueError("Nested COMPOSITE patches are not allowed")
        return self


# =====================================================
# Discriminated Union
# =====================================================

Patch = Annotated[
    Union[
        AddCardPatch,
        RemoveCardPatch,
        MoveCardPatch,
        SwapCardsPatch,
        ResizeCardPatch,
        ChangeColorPatch,
        ChangeTitlePatch,
        ChangeChartTypePatch,
        UpdateSqlPatch,
        AddFilterPatch,
        RemoveFilterPatch,
        RollbackToVersionPatch,
    ],
    Field(discriminator="patch_type"),
]


PATCH_TYPES = {
    "ADD_CARD",
    "REMOVE_CARD",
    "MOVE_CARD",
    "SWAP_CARDS",
    "RESIZE_CARD",
    "CHANGE_COLOR",
    "CHANGE_TITLE",
    "CHANGE_CHART_TYPE",
    "UPDATE_SQL",
    "ADD_FILTER",
    "REMOVE_FILTER",
    "ROLLBACK_TO_VERSION",
    "COMPOSITE",
}


def parse_patch(data: dict) -> Any:
    """
    Parse a dict into the correct Patch model (or Composite).
    Raises ValueError if patch_type is unknown.
    """
    ptype = data.get("patch_type")
    if not ptype:
        raise ValueError("Missing 'patch_type'")

    if ptype == "COMPOSITE":
        inner = [parse_patch(p) for p in data.get("patches", [])]
        return CompositePatch(patches=inner)

    mapping = {
        "ADD_CARD": AddCardPatch,
        "REMOVE_CARD": RemoveCardPatch,
        "MOVE_CARD": MoveCardPatch,
        "SWAP_CARDS": SwapCardsPatch,
        "RESIZE_CARD": ResizeCardPatch,
        "CHANGE_COLOR": ChangeColorPatch,
        "CHANGE_TITLE": ChangeTitlePatch,
        "CHANGE_CHART_TYPE": ChangeChartTypePatch,
        "UPDATE_SQL": UpdateSqlPatch,
        "ADD_FILTER": AddFilterPatch,
        "REMOVE_FILTER": RemoveFilterPatch,
        "ROLLBACK_TO_VERSION": RollbackToVersionPatch,
    }
    model = mapping.get(ptype)
    if not model:
        raise ValueError(f"Unknown patch_type: {ptype}")
    return model(**data)