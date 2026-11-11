# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class CordisProjectRow:
    __record_set__: ClassVar[str] = "cordis_projects.jsonl#cordis_projects"
    __source_digest__: ClassVar[str] = "560f640d8555f49dda7fbe7c607aa11d91f222afb8ddbffa604a31b1203e34ad"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    grant_id: str
    acronym: str
    title: str | None = None
    start: str | None = None
    end: str | None = None
    total_cost_eur: float | None = None
    eu_contribution_eur: float | None = None
    coordinator: str | None = None
    objective: str | None = None
