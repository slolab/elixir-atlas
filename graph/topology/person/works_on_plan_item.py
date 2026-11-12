from dataclasses import dataclass, field
from typing import ClassVar

from ..plan_item.node import PlanItemId
from .node import PersonId


@dataclass(frozen=True)
class WorksOnPlanItem:
    """A person a source names on a work package, task, deliverable or other plan item. role 'lead': named as its
    lead, or holding a lead role in the work package or task of that code; when a page names more than three leads
    for one task (the STEERS and CONVERGE pages list every partner under a task's 'Leadership'), they are
    participants. role 'participant': listed among its participants or partners."""

    schema_id: ClassVar[str] = "atlas:works_on_plan_item"
    id: str
    source: PersonId
    target: PlanItemId
    role: str = field(metadata={"description": "lead or participant."})
    as_written: str = field(
        metadata={
            "description": "The person as the source writes them, e.g. 'Ludek Matyska/CZ-MUNI', 'EE-UTAR (Priit Adler)'."
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
