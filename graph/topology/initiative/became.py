from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class Became:
    """The group became this group or moved its activities to this group or project, as the ELIXIR directory or
    the group's archived page states, e.g. a Focus Group that became a Community, or Marine Metagenomics, which
    became the Microbiome Community. The source group is past; its earlier facts stay on it."""

    schema_id: ClassVar[str] = "atlas:became"
    id: str
    source: InitiativeId
    target: InitiativeId
    date: str | None = field(metadata={"description": "When, as YYYY-MM."})
    evidence: str | None = field(metadata={"description": "What the ELIXIR directory states, restated as '<group> became the <target>'."})
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
