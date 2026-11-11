from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import ElixirNodeId


@dataclass(frozen=True)
class TakesPartIn:
    """A source states that the Node takes part in the group or project; one edge per Node, source and spelling. Count distinct Nodes over these edges for the number of Nodes; the ELIXIR Hub and EMBL-EBI count as Nodes here, so exclude elixir_node.kind 'hub' when counting member Nodes."""

    schema_id: ClassVar[str] = "atlas:takes_part_in"
    id: str
    source: ElixirNodeId
    target: InitiativeId
    as_written: str = field(
        metadata={"description": "The Node as the source writes it."}
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
