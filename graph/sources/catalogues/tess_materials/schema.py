# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import DOI, EDAM_TOPIC_URIS


@dataclass(frozen=True, kw_only=True)
class TessMaterial:
    __record_set__: ClassVar[str] = "tess_materials.jsonl#tess_materials"
    __source_digest__: ClassVar[str] = "e5733b73c7c2d0e0211c03643111f226261e99331264652ce988c7440593f72a"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    authors: list[str]
    collection_ids: list[str]
    content_provider_id: str | None
    date_published: str | None
    description: str | None
    doi: str | None = source_field("doi", term=DOI)
    keywords: list[str]
    node_ids: list[str]
    resource_types: list[str]
    source_path: str
    tess_id: str
    title: str | None
    topic_labels: list[str]
    edam_topic_uris: list[str] = source_field("topic_uris", term=EDAM_TOPIC_URIS)
    url: str | None
