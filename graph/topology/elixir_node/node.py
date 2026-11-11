from dataclasses import dataclass, field
from typing import ClassVar, NewType


ElixirNodeId = NewType("ElixirNodeId", str)


@dataclass(frozen=True)
class ElixirNode:
    """An ELIXIR Node (a member country's national bioinformatics infrastructure, or EMBL-EBI) or the ELIXIR
    Hub, from the closed list of members on elixir-europe.org (Malta and Slovakia are listed as members but have no
    Node page yet). Sources name Nodes in many ways ('ELIXIR Portugal',
    'Portugal', 'PT', 'BioData.pt', 'de.NBI'); each name read as this Node is listed in aliases. Organisations are
    not Nodes: a person at SIB or CSC is linked to a Node only where a source names the Node."""

    schema_id: ClassVar[str] = "atlas:elixir_node"
    id: ElixirNodeId
    name: str = field(
        metadata={
            "description": "The Node's name as elixir-europe.org writes it, e.g. 'ELIXIR Portugal'."
        }
    )
    kind: str = field(metadata={"description": "member_node, embl_ebi or hub."})
    country: str | None = field(metadata={"description": "Country of a member Node."})
    aliases: list[str] = field(
        metadata={
            "description": "Names and codes that sources use and that were read as this Node."
        }
    )
