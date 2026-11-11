from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class RelatedTo:
    """A source names the target as involved in, linked to or the parent of the source initiative. The kind of link (parent, partner, mention) is not recorded."""

    schema_id: ClassVar[str] = "atlas:related_to"
    id: str
    source: InitiativeId
    target: InitiativeId
    as_written: str = field(
        metadata={
            "description": "The related group or project as the source writes it."
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
