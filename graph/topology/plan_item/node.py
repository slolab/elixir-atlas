from dataclasses import dataclass, field
from typing import ClassVar, NewType


PlanItemId = NewType("PlanItemId", str)


@dataclass(frozen=True)
class PlanItem:
    """A unit of planned or reported work of one initiative: work package, task or activity, deliverable,
    milestone, event, output, goal, roadmap action or item reported as still open. Items of one initiative with
    the same code (or, without a code, the same kind and title) from several documents are one plan item; the
    value each source states for the date is kept in date_statements. Extracted with a language model and
    checked against a verbatim quote."""

    schema_id: ClassVar[str] = "atlas:plan_item"
    id: PlanItemId
    kind: str = field(
        metadata={
            "description": "work_package, task, deliverable, milestone, event, output, goal, action or open_item."
        }
    )
    code: str | None = field(
        metadata={
            "description": "Identifier as written, e.g. 'WP4', 'Activity 1', 'D1.6', 'M2.1'."
        }
    )
    label: str = field(metadata={"description": "Title as written."})
    description: str | None = field(
        metadata={"description": "What it is or does, close to the source's wording."}
    )
    parent: str | None = field(
        metadata={
            "description": "Code or title of the work package or task it belongs to."
        }
    )
    date: str | None = field(
        metadata={
            "description": "Due, planned or held date (YYYY, YYYY-MM or YYYY-MM-DD) when the sources agree within a month; a project month such as 'M36' is counted from the project's start when that is known to the month. Null when sources disagree (see review_item) or no date can be derived."
        }
    )
    date_as_written: str | None = field(
        metadata={
            "description": "The date as the first source writes it, e.g. 'M12', 'December 2026'."
        }
    )
    date_statements: list[str] = field(
        metadata={"description": "Each source's date as 'value | source URL'."}
    )
    status: str = field(
        metadata={
            "description": "Status the sources state: planned, ongoing, done, delayed, open or not_stated."
        }
    )
    leads: list[str] = field(
        metadata={"description": "Leading people, organisations or Nodes, as written."}
    )
    participants: list[str] = field(
        metadata={
            "description": "Contributing Nodes, organisations, groups or people, as written."
        }
    )
    effort: str | None = field(
        metadata={
            "description": "Effort stated, e.g. '12 PM'; null when no source states it."
        }
    )
    link: str | None = field(metadata={"description": "URL a source gives for it."})
    sources: list[str] = field(
        metadata={"description": "URLs of the documents that state it."}
    )
    evidence: str | None = field(
        metadata={"description": "Verbatim excerpt of the first source that states it."}
    )
