# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class ElectionCandidateRow:
    __record_set__: ClassVar[str] = "election_candidates.jsonl#election_candidates"
    __source_digest__: ClassVar[str] = "358ac4db4fca433904bf7cecfb402afc9344c893a1e62d15ffd8e0ebe30d7f9f"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    community: str
    person: str
    country: str | None = None
    affiliation: str | None = None
    note: str | None = None
    year: int
