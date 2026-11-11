from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import OrganisationId


@dataclass(frozen=True)
class ParticipatesIn:
    """An organisation's participation in an EU project as its CORDIS fact sheet lists it."""

    schema_id: ClassVar[str] = "atlas:participates_in"
    id: str
    source: OrganisationId
    target: InitiativeId
    participation: str = field(
        metadata={
            "description": "coordinator, participant (beneficiary) or partner (associated partner, no EU contribution)."
        }
    )
    participation_ended: bool = field(
        metadata={"description": "True when CORDIS marks the participation as ended."}
    )
    net_eu_contribution_eur: float | None = field(
        metadata={
            "description": "Net EU contribution to the organisation in euro; says nothing about which of its people are funded."
        }
    )
    total_cost_eur: float | None = field(
        metadata={
            "description": "Total cost of the organisation's participation in euro."
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
