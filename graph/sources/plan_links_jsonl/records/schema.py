# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class PlanLinkRow:
    __record_set__: ClassVar[str] = "plan_links.jsonl#plan_links"
    __source_digest__: ClassVar[str] = "d47ddc5fc3d254237e5239ec2e28d8a61ce2ebac2dbe53625966e90a9c31628d"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    owner: str
    linked_project: str
    relation: str
    item: str | None = None
    linked_item: str | None = None
