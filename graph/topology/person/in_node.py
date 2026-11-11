from dataclasses import dataclass, field
from typing import ClassVar

from ..elixir_node.node import ElixirNodeId
from .node import PersonId


@dataclass(frozen=True)
class InNode:
    """A source places the person in this ELIXIR Node or the Hub: next to their name, in a Node's team page, or as their Node role."""

    schema_id: ClassVar[str] = "atlas:in_node"
    id: str
    source: PersonId
    target: ElixirNodeId
    as_written: str = field(
        metadata={"description": "The Node as the source writes it."}
    )
    role: str | None = field(
        metadata={
            "description": "The person's position in the Node as written, e.g. 'Head of Node'; null when the source only places them there (a Node named next to them, a Node code such as 'CH-SIB' or '(PT)' in their affiliation, or a Node team page)."
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
