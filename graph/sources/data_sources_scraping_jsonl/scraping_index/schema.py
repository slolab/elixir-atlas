# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class ScrapingIndexRow:
    __record_set__: ClassVar[str] = "data-sources-scraping.jsonl#data-sources-scraping"
    __source_digest__: ClassVar[str] = "5a3d27dc191c8ad41923134f29724692efbc5fea60be267265b15d48a9b04945"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    bytes: int | None
    content_type: str | None
    discovered_from: str | None
    discovery_status: str | None
    error: str | None
    final_url: str | None
    links: int | None
    note: str | None
    path: str | None
    previous_path: str | None
    reason: str | None
    representation: str | None
    retrieved_at: str | None
    reviewed_at: str | None
    source: str
    status: str
    updated_at: str | None
    url: str | None
