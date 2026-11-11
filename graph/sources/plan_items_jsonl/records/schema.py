# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class PlanItemRow:
    __record_set__: ClassVar[str] = "plan_items.jsonl#plan_items"
    __source_digest__: ClassVar[str] = "a195e6c0b1758f58e4c1656e39827f59f57f1be88327a433e5dfaeef7b01f5df"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    owner: str
    kind: str
    code: str | None = None
    label: str
    description: str | None = None
    parent: str | None = None
    date: str | None = None
    date_as_written: str | None = None
    status: str
    leads: list[str]
    participants: list[str]
    effort: str | None = None
    link: str | None = None
    topics: list[str]
