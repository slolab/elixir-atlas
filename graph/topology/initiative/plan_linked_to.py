from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class PlanLinkedTo:
    """A work plan, page or report states that the source initiative's work, or one of its work packages, tasks
    or deliverables, is linked to the target initiative or one of its work items: complements, builds on,
    contributes to, is aligned with, is delivered together with. This is where a stated overlap between two
    projects is written down. Stored in both directions so a query from either side finds it: direction 'stated'
    runs from the initiative whose document states the link, 'reverse' runs back. Projects that only share a
    topic, with no such statement, have no plan link."""

    schema_id: ClassVar[str] = "atlas:plan_linked_to"
    id: str
    source: InitiativeId
    target: InitiativeId
    direction: str = field(metadata={"description": "stated or reverse; see the edge description."})
    item: str | None = field(
        metadata={"description": "The source initiative's work item the link is about, code and title as written; null for its work as a whole."}
    )
    item_id: str | None = field(metadata={"description": "The plan_item id of item, when the build matched its code."})
    linked_item: str | None = field(
        metadata={"description": "The target initiative's work item, code and title as written; null when only the initiative is named."}
    )
    linked_item_id: str | None = field(metadata={"description": "The plan_item id of linked_item, when the build matched its code."})
    relation: str = field(metadata={"description": "How the statement links them, close to its wording, e.g. 'complementary links'."})
    quote: str | None = field(metadata={"description": "The statement, verbatim."})
    source_url: str | None = field(metadata={"description": "URL of the document that states the link."})
    source_document: str | None = field(metadata={"description": "Identifier of that document in the source_document table."})
