from dataclasses import dataclass, field
from typing import ClassVar, NewType


ReviewPaperId = NewType("ReviewPaperId", str)


@dataclass(frozen=True)
class ReviewPaper:
    """A review article from Europe PMC whose title or abstract mentions 'systems biology', published from 2022
    to 10 November 2026: an external baseline for the state of the art of the field, not ELIXIR output."""

    schema_id: ClassVar[str] = "atlas:review_paper"
    id: ReviewPaperId
    title: str | None = field(metadata={"description": "Title."})
    journal: str | None = field(metadata={"description": "Journal."})
    year: str | None = field(metadata={"description": "Publication year."})
    date: str | None = field(metadata={"description": "First publication date."})
    doi: str | None = field(metadata={"description": "DOI."})
    authors: list[str] = field(metadata={"description": "Author names."})
    keywords: list[str] = field(metadata={"description": "Author keywords."})
    mesh_terms: list[str] = field(metadata={"description": "MeSH descriptors."})
    abstract: str | None = field(metadata={"description": "Abstract."})
    cited_by_count: int | None = field(
        metadata={"description": "Citations Europe PMC counts."}
    )
