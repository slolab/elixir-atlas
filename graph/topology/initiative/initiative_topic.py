from dataclasses import dataclass, field
from typing import ClassVar

from ..topic.node import TopicId
from .node import InitiativeId


@dataclass(frozen=True)
class InitiativeTopic:
    """An EDAM topic a language model assigned from a source's description of the initiative; an interpretation, not a source's own tag."""

    schema_id: ClassVar[str] = "atlas:initiative_topic"
    id: str
    source: InitiativeId
    target: TopicId
    evidence: str | None = field(
        metadata={"description": "Verbatim excerpt the assignment rests on."}
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
