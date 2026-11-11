from dataclasses import dataclass, field
from typing import ClassVar, NewType


ReviewItemId = NewType("ReviewItemId", str)


@dataclass(frozen=True)
class ReviewItem:
    """A question the sources leave open, for manual resolution: a possible match between two people,
    organisations or initiatives that the build did not join (person_match, organisation_match,
    initiative_match), or values that sources state differently (value_conflict: dates more than a month apart,
    different leads, Nodes, people or work package leads). The id is stable across builds while the question is
    the same. A decision recorded against its id in data/input/review-decisions.csv is applied by the next build:
    'same' joins two entries (the item then disappears, and the joined entry lists 'decision' in identity_basis),
    'different' keeps them apart, and a chosen date replaces the null start, end or date. Decided items are
    exported with status resolved."""

    schema_id: ClassVar[str] = "atlas:review_item"
    id: ReviewItemId
    kind: str = field(
        metadata={
            "description": "person_match, organisation_match, initiative_match or value_conflict."
        }
    )
    question: str = field(metadata={"description": "The question in plain words."})
    subjects: list[str] = field(
        metadata={
            "description": "Identifiers of the atlas entries the question is about."
        }
    )
    subject_names: list[str] = field(
        metadata={"description": "Names of those entries."}
    )
    property: str | None = field(
        metadata={
            "description": "For a value_conflict, the property in question, e.g. end."
        }
    )
    options: list[str] = field(
        metadata={
            "description": "Each candidate value or match with its source, as 'value | source URL'."
        }
    )
    status: str = field(metadata={"description": "open or resolved."})
    decision: str | None = field(
        metadata={
            "description": "The recorded decision from data/input/review-decisions.csv, when resolved."
        }
    )
