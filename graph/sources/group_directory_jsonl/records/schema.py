# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class GroupDirectoryRow:
    __record_set__: ClassVar[str] = "group_directory.jsonl#group_directory"
    __source_digest__: ClassVar[str] = "6d3350608ae6c2ed10b9dee6a096e10783f44e7630e2eb9e7662a8d4d93294a1"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    name: str
    kind: str
    status: str
    url: str
    start: str | None = None
    end: str | None = None
    became: str | None = None
    became_date: str | None = None
