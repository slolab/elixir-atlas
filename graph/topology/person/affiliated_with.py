from dataclasses import dataclass, field
from typing import ClassVar

from ..organisation.node import OrganisationId
from .node import PersonId


@dataclass(frozen=True)
class AffiliatedWith:
    """A source gives this organisation as the person's affiliation."""

    schema_id: ClassVar[str] = "atlas:affiliated_with"
    id: str
    source: PersonId
    target: OrganisationId
    as_written: str = field(
        metadata={"description": "The affiliation as the source writes it."}
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
