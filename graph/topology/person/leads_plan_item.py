from dataclasses import dataclass, field
from typing import ClassVar

from ..plan_item.node import PlanItemId
from .node import PersonId


@dataclass(frozen=True)
class LeadsPlanItem:
    """A person named as lead of a work package, task, deliverable or other plan item."""

    schema_id: ClassVar[str] = "atlas:leads_plan_item"
    id: str
    source: PersonId
    target: PlanItemId
    as_written: str = field(
        metadata={
            "description": "The lead as the source writes it, e.g. 'Ludek Matyska/CZ-MUNI'."
        }
    )
    source_url: str | None = field(
        metadata={
            "description": "URL of the page or document that states this, from the scraping index."
        }
    )
    retrieved_at: str | None = field(
        metadata={
            "description": "When that page or document was retrieved (ISO 8601 UTC)."
        }
    )
    source_document: str | None = field(
        metadata={
            "description": "Identifier of that document in the source_document table."
        }
    )
