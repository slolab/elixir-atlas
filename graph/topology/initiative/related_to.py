from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class RelatedTo:
    """A source links the two initiatives: it names one as involved in, linked to or the parent of the other. Every
    link is stored in both directions, so a query from either side finds it: direction 'stated' runs from the
    initiative whose page or document names the other, 'reverse' runs back. Count distinct initiatives, not edges.
    The kind of link (parent, partner, mention) is not recorded."""

    schema_id: ClassVar[str] = "atlas:related_to"
    id: str
    source: InitiativeId
    target: InitiativeId
    as_written: str = field(
        metadata={
            "description": "The other initiative's name as the stating source writes it (for direction 'reverse', the stating initiative's name)."
        }
    )
    direction: str = field(
        metadata={
            "description": "stated: the source initiative's page or document names the target. reverse: the same statement read from the target's side."
        }
    )
    quote: str | None = field(
        metadata={"description": "The stating source's sentence that names the other initiative, verbatim, when the extracted quote contains the name; null otherwise."}
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
