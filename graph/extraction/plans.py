from dataclasses import dataclass, field
from typing import ClassVar, Literal

from ._llm import MODEL, LlmExtractor

PlanKind = Literal[
    "work_package", "task", "deliverable", "milestone", "event", "output", "goal", "action", "open_item"
]


@dataclass(frozen=True, kw_only=True)
class PlanItem:
    """A unit of planned or reported work of an ELIXIR group or project, as one document states it: work
    packages, tasks and activities, deliverables and milestones, events (meetings, workshops, hackathons, webinars,
    courses), outputs (publications, tools, standards, guidelines, reports), goals and roadmap actions, and items
    reported as still open. One record per item. Leave out general background and work of organisations outside
    ELIXIR."""

    __record_key__: ClassVar[tuple[str, ...]] = ("owner", "kind", "label")

    owner: str = field(
        metadata={
            "description": "The ELIXIR group or project the item belongs to, as written, e.g. 'ELIXIR-STEERS', "
            "'Systems Biology Community', 'ELIXIR Compute Platform (2024-26)'."
        }
    )
    kind: PlanKind = field(
        metadata={
            "description": "work_package, task (including numbered activities), deliverable, milestone, event, "
            "output, goal (an aim or ambition), action (a planned step or follow-up) or open_item (reported as "
            "not yet done)."
        }
    )
    code: str | None = field(
        metadata={"description": "Its identifier as written, e.g. 'WP4', 'T4.2', 'Activity 1', 'D1.6', 'M2.1'."}
    )
    label: str = field(
        metadata={
            "description": "Its title as written; for an item without a title, a short phrase close to the "
            "document's wording."
        }
    )
    description: str | None = field(
        metadata={"description": "What it is or does, close to the document's wording, up to about 60 words."}
    )
    parent: str | None = field(
        metadata={"description": "Code or title of the work package or task it belongs to."}
    )
    date: str | None = field(
        metadata={
            "description": "Its due, planned or held date as YYYY, YYYY-MM or YYYY-MM-DD (for an event, its "
            "start), only as precise as the document; null when the document gives only a project month."
        }
    )
    date_as_written: str | None = field(
        metadata={"description": "The date or period exactly as written, e.g. 'M12', 'Q3 2026', 'December 2026'."}
    )
    status: Literal["planned", "ongoing", "done", "delayed", "open", "not_stated"] = field(
        metadata={"description": "Status as the document states it; not_stated when it does not."}
    )
    leads: list[str] = field(
        metadata={"description": "People, organisations or Nodes stated as leading it, as written."}
    )
    participants: list[str] = field(
        metadata={
            "description": "Nodes, organisations, groups or people stated as contributing to it, other than the "
            "leads, as written."
        }
    )
    effort: str | None = field(metadata={"description": "Effort stated for it, as written, e.g. '12 PM'."})
    link: str | None = field(metadata={"description": "URL the document gives for it."})
    topics: list[str] = field(
        metadata={
            "description": "EDAM topics, only from the list in the instructions, that its title or description "
            "directly supports; at most 4."
        }
    )


class PlanReader(LlmExtractor):
    name = "plan-reader"
    version = "1"
    settings = {"model": MODEL, "reasoning": "low"}
    uses_topics = True
    max_topics = 4
    instructions = (
        "Work plans and handbooks list work packages, tasks, deliverables and milestones in tables: give every "
        "row its own record with its code, due date and leads. Event reports and roadmaps state goals, "
        "follow-up actions, planned events and outputs, and items still open: give each its own record. Group "
        "and project pages list related or upcoming events and outputs: give each its own record with its date. "
        "Use the group's or project's name as the owner, not the name of the document."
    )
