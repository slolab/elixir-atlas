from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import PersonId


@dataclass(frozen=True)
class InvolvedIn:
    """Everything the public sources say about one person's part in one group or project, gathered into one
    edge: their roles, the plan items they lead or work on, their outputs and credited tools for it, and their
    Nodes and organisations. It is derived from holds_role, works_on_plan_item, authored with output_of, and
    credited_for_tool with tool_for or recommends, so it is the place to list a group's or project's people, a
    person's involvement, or a Node's people on a project (filter on nodes). People appear only where a public
    source names them: for Communities this is a lower bound, never the membership."""

    schema_id: ClassVar[str] = "atlas:involved_in"
    id: str
    source: PersonId
    target: InitiativeId
    leadership: bool = field(
        metadata={"description": "True when a role is co_lead, lead, chair, coordinator, deputy, liaison, work_package_lead or task_lead, or the person leads one of its plan items. Election candidates are not leaders."}
    )
    roles: list[str] = field(
        metadata={"description": "Each distinct role as 'role_kind: role as written (work item)', e.g. 'co_lead: Community co-lead', 'work_package_lead: WP leader (WP5)', 'candidate: Co-lead candidate'."}
    )
    plan_items: list[str] = field(
        metadata={"description": "Plan items of the initiative the person works on, as 'lead: code label' or 'participant: code label'."}
    )
    outputs: list[str] = field(
        metadata={"description": "Outputs of the initiative (output_of other than by description) the person authored, as 'date title', newest first, at most ten."}
    )
    tools: list[str] = field(
        metadata={"description": "bio.tools entries that credit the person (developer, maintainer, contact or other), by name, at most 30. Entries the initiative also tags (tool_for) or recommends end in ' [this initiative]'; the others are the person's tools from bio.tools credits, whether or not they are linked to the initiative. The credit is matched to the person record by the build."}
    )
    nodes: list[str] = field(metadata={"description": "The person's ELIXIR Nodes from in_node, by name."})
    organisations: list[str] = field(metadata={"description": "The person's organisations from affiliated_with, by name."})
    bases: list[str] = field(
        metadata={"description": "Which sources the involvement rests on: role, candidate, plan_item, author, tool_credit."}
    )
    source_urls: list[str] = field(metadata={"description": "Up to five URLs of the pages or documents that state the roles and plan items."})
