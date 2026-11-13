import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from biotope.extraction import Document, Schema

from ._llm import MODEL, LlmExtractor
from ._reading import document_text

WORK_ITEM = re.compile(r"\b(?:WP|Work ?Package|Task|T)\s?\d+(?:\.\d+)?\b")


@dataclass(frozen=True, kw_only=True)
class PlanLink:
    """A statement in a group's or project's work plan, page or report that links its work, or one of its work
    packages, tasks, activities or deliverables, to another ELIXIR project or group, or to a work package, task or
    deliverable of another project: complements, builds on, contributes to, feeds into, is aligned with, is
    delivered together with. One record per linked pair. Leave out links between work items of the same project,
    funding acknowledgements, and lists of partners or related projects that state no shared work."""

    __record_key__: ClassVar[tuple[str, ...]] = ("owner", "item", "linked_project", "linked_item")

    owner: str = field(
        metadata={"description": "The group or project whose work the statement describes, by its name, e.g. 'ELIXIR Training Platform'."}
    )
    item: str | None = field(
        metadata={
            "description": "The owner's work package, task, activity or deliverable the link is about, with its code "
            "and title as written, e.g. 'WP4 Train-the-Trainer programme consolidation'. Null when the link is "
            "about the owner's work as a whole."
        }
    )
    linked_project: str = field(
        metadata={"description": "The other project or group, by its name, e.g. 'ELIXIR-STEERS', 'Galaxy Community'."}
    )
    linked_item: str | None = field(
        metadata={
            "description": "The other project's work package, task or deliverable, with code and title as written, "
            "e.g. 'WP4 Task 4.3 Capacity building in training skills for ELIXIR Node staff'. Null when the "
            "statement names only the project or group."
        }
    )
    relation: str = field(
        metadata={"description": "How the statement links them, as a short phrase close to its wording, e.g. 'complementary links', 'builds on', 'in collaboration with'."}
    )


class PlanLinkReader(LlmExtractor):
    name = "plan-link-reader"
    version = "1"
    settings = {"model": MODEL, "reasoning": "low"}
    instructions = (
        "Look for sentences that tie this project's work to another project's work, such as 'complementary links to "
        "ELIXIR-STEERS WP4, specifically Task 4.3' or 'builds on Training Platform resources'. When one sentence names "
        "several tasks of the other project, give one record per task. Give the owner and the linked project by their "
        "ELIXIR names, not the document title."
    )

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        if not WORK_ITEM.search(document_text(document.path)):
            return []
        return super().extract(document, schema)
