from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class PartOf:
    """The group or project is part of the target: a sub-project of a programme or Commissioned Service, or a
    sub-group of a Community or Platform. Distinct from related_to, which only says that one names the other."""

    schema_id: ClassVar[str] = "atlas:part_of"
    id: str
    source: InitiativeId
    target: InitiativeId
    basis: str = field(
        metadata={
            "description": "sub_page: the source's own page sits under the target's page (e.g. /science/bfsp/biodiv under "
            "/science/bfsp); work_plan: the target's work plan has a work package for the source."
        }
    )
    source_url: str | None = field(metadata={"description": "The page or document that shows the relation."})
