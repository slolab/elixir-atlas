from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import ElixirNodeId


@dataclass(frozen=True)
class TakesPartIn:
    """The Node takes part in the group or project; one edge per Node, source, spelling and basis. basis 'own_page':
    the initiative's own main page (pages[0]) lists the Node, which is the current official list. basis 'stated':
    another source lists it: an older or secondary page, a Node website, a work plan or a report; such a Node may
    have left or the source may be out of date, so compare with own_page before reporting it as current. basis
    'beneficiary_country': a CORDIS beneficiary of the EU project is in the Node's country (or is the Node's own
    institute, such as EMBL-EBI); this links ELIXIR's EU grants to Nodes, but the beneficiary is an organisation, so
    check its name before calling it the Node's institute. basis 'lead_node': a current lead, co-lead or Platform coordinator of the group belongs to
    the Node, as the group's page states; this is an inference, not a Node list. Count distinct Nodes over these
    edges for the number of Nodes, filtering on basis as needed; the ELIXIR Hub and EMBL-EBI count as Nodes here,
    so exclude elixir_node.kind 'hub' when counting member Nodes."""

    schema_id: ClassVar[str] = "atlas:takes_part_in"
    id: str
    source: ElixirNodeId
    target: InitiativeId
    as_written: str = field(
        metadata={"description": "The Node as the source writes it; for lead_node, the lead's name and Node."}
    )
    basis: str = field(metadata={"description": "own_page, stated, beneficiary_country or lead_node."})
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
