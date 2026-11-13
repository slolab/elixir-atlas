from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import ElixirNodeId


@dataclass(frozen=True)
class NodeInvolvedIn:
    """One Node's involvement in one group or project, gathered into one edge: whether the initiative's own page
    lists the Node, which other sources list it, which EU beneficiaries in its country take part, and which of
    its people hold roles or plan items there. It is derived from takes_part_in, participates_in and involved_in,
    so it is the Node's portfolio: one row per initiative. bases says how strong the link is: own_page (the current
    official list), stated (another source: an older page, a Node site, a work plan), beneficiary_country (an EU
    beneficiary in the Node's country), lead_node (a lead's Node) and people (only people of the Node are named
    there). It does not state whether the Node's work is funded or in-kind."""

    schema_id: ClassVar[str] = "atlas:node_involved_in"
    id: str
    source: ElixirNodeId
    target: InitiativeId
    bases: list[str] = field(metadata={"description": "own_page, stated, beneficiary_country, lead_node, people; see the edge description."})
    listed_on_own_page: bool = field(metadata={"description": "True when the initiative's own main page lists the Node."})
    initiative_kind: str = field(metadata={"description": "The initiative's kind, copied for filtering."})
    period: str | None = field(metadata={"description": "The initiative's start and end as 'start to end', copied for filtering."})
    period_status: str | None = field(metadata={"description": "The initiative's period_status (ended, running, not_started), copied."})
    beneficiaries: list[str] = field(
        metadata={"description": "EU beneficiaries in the Node's country, as 'organisation (participation; net EU contribution EUR)'."}
    )
    people: list[str] = field(
        metadata={"description": "People of the Node involved, as 'name: roles; plan items', leaders first, at most 25."}
    )
    node_site: str | None = field(
        metadata={
            "description": "listed: a page of the Node's own website names the initiative. not_listed: the Atlas collected the Node's project listing (ELIXIR-UK, de.NBI, ELIXIR CZ, Luxembourg, the Netherlands and Norway) and none of its pages names the initiative, so the Node's site and the initiative's page disagree or the listing is out of date. Null when no project listing of the Node was collected."
        }
    )
    limits: str = field(metadata={"description": "What public sources cannot tell about the Node's part; report it when a question asks about commitments or funding."})
    plan_summary: str | None = field(
        metadata={
            "description": "When the initiative has plan items (work packages, tasks, deliverables): how many the Node or its people lead and how many more they work on, e.g. 'Leads 0 of the 120 plan items; works on 4 more'. A lead count of 0 means no collected plan names the Node or its people as a lead. Null when the initiative has no plan items."
        }
    )
    leads_plan_items: list[str] = field(
        metadata={"description": "The plan items the Node or its people lead, as 'code label (via the Node name or person as the plan states it)', at most 40."}
    )
    works_on_plan_items: list[str] = field(
        metadata={"description": "The plan items the Node or its people work on without leading them, in the same form, at most 40."}
    )
    sources: list[str] = field(metadata={"description": "Up to six URLs of the sources that list the Node."})
