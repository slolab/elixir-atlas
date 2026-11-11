# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import DOI, ORCIDS, PERSON_NAMES


@dataclass(frozen=True, kw_only=True)
class ZenodoRecord:
    __record_set__: ClassVar[str] = "zenodo_records.jsonl#zenodo_records"
    __source_digest__: ClassVar[str] = "a5cd4629035ed0e9311308ebbc28054cf5986a4deafceb83cd80c73f069a1f2d"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    communities: list[str]
    concept_doi: str | None
    concept_record_id: str | None
    creator_affiliations: list[str]
    person_names: list[str] = source_field("creator_names", term=PERSON_NAMES)
    orcids: list[str] = source_field("creator_orcids", term=ORCIDS)
    description: str | None
    doi: str | None = source_field("doi", term=DOI)
    file_names: list[str]
    grant_acronyms: list[str]
    grant_codes: list[str]
    keywords: list[str]
    publication_date: str | None
    record_id: str
    resource_type: str | None
    source_path: str
    source_paths: list[str]
    title: str | None
    url: str | None
    version: str | None
