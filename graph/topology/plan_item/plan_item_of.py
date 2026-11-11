from dataclasses import dataclass
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import PlanItemId


@dataclass(frozen=True)
class PlanItemOf:
    """The plan item belongs to this initiative."""

    schema_id: ClassVar[str] = "atlas:plan_item_of"
    id: str
    source: PlanItemId
    target: InitiativeId
