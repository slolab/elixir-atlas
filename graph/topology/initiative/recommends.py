from dataclasses import dataclass, field
from typing import ClassVar

from ..resource.node import ResourceId
from .node import InitiativeId


@dataclass(frozen=True)
class Recommends:
    """The group's own page or paper points readers to the resource as one to use in its field: it recommends,
    endorses, lists or develops it. Every edge is a recommendation by the group's own documents; this is what
    separates it from a catalogue entry (a bio.tools tag or TeSS listing alone: tool_for, event_for, material_for).
    basis 'develops': the group or its members build or maintain the resource; 'recommends': any other pointer.
    The quote is in evidence; the basis is a language model's reading of it."""

    schema_id: ClassVar[str] = "atlas:recommends"
    id: str
    source: InitiativeId
    target: ResourceId
    basis: str = field(metadata={"description": "recommends or develops (the group or its members build or maintain it)."})
    resource_as_written: str = field(metadata={"description": "The resource's name as this document writes it."})
    purpose: str | None = field(metadata={"description": "What the document says the resource is for."})
    url: str | None = field(metadata={"description": "The link the document gives for the resource."})
    evidence: str | None = field(metadata={"description": "The sentence the recommendation is read from."})
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
