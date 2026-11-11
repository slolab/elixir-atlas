# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import DOI, ORCIDS, PERSON_NAMES


@dataclass(frozen=True, kw_only=True)
class EuropepmcReview:
    __record_set__: ClassVar[str] = "europepmc_reviews.jsonl#europepmc_reviews"
    __source_digest__: ClassVar[str] = "60dad81f90ebf3491e0c800a456e0d5d4a1262c6c481fe7a6ea377f671f2f53d"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    abstract: str | None
    person_names: list[str] = source_field("author_names", term=PERSON_NAMES)
    orcids: list[str] = source_field("author_orcids", term=ORCIDS)
    cited_by_count: int | None
    doi: str | None = source_field("doi", term=DOI)
    epmc_id: str
    first_publication_date: str | None
    journal: str | None
    keywords: list[str]
    mesh_terms: list[str]
    pmid: str | None
    pub_year: str | None
    source_path: str
    title: str | None
