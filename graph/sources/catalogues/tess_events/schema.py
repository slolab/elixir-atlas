# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import EDAM_TOPIC_URIS


@dataclass(frozen=True, kw_only=True)
class TessEvent:
    __record_set__: ClassVar[str] = "tess_events.jsonl#tess_events"
    __source_digest__: ClassVar[str] = "adf7de05b984a7aa4666e2d39cd22b8a5f3eb68e82306cedd62a519045970ad5"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    city: str | None
    collection_ids: list[str]
    content_provider_id: str | None
    country: str | None
    description: str | None
    end: str | None
    event_types: list[str]
    host_institutions: list[str]
    keywords: list[str]
    node_ids: list[str]
    online: bool | None
    organizer: str | None
    source_path: str
    start: str | None
    tess_id: str
    tess_url: str
    title: str | None
    topic_labels: list[str]
    edam_topic_uris: list[str] = source_field("topic_uris", term=EDAM_TOPIC_URIS)
    url: str | None
