# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import DOI, PERSON_NAMES


@dataclass(frozen=True, kw_only=True)
class F1000Item:
    __record_set__: ClassVar[str] = "f1000_items.jsonl#f1000_items"
    __source_digest__: ClassVar[str] = "dfb9a55851186c3b097096b995905b4590e149de7f572084d736530101f8eb14"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    person_names: list[str] = source_field("creator_names", term=PERSON_NAMES)
    date: str | None
    description: str | None
    doi: str | None = source_field("doi", term=DOI)
    item_path: str
    kind: str
    source_path: str
    subjects: list[str]
    title: str | None
