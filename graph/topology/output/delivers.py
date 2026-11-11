from dataclasses import dataclass, field
from typing import ClassVar

from ..plan_item.node import PlanItemId
from .node import OutputId


@dataclass(frozen=True)
class Delivers:
    """The output is the published version of this deliverable, milestone or other plan item."""

    schema_id: ClassVar[str] = "atlas:delivers"
    id: str
    source: OutputId
    target: PlanItemId
    basis: str = field(
        metadata={
            "description": "Why: link (the plan item's link points to the output) or code (the output's title names the item's code; when the record names the project's grant, the title shares a word with the item's label or is too short to compare; otherwise it repeats at least half of the label's words)."
        }
    )
