# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class RecommendationRow:
    __record_set__: ClassVar[str] = "recommendations.jsonl#recommendations"
    __source_digest__: ClassVar[str] = "c9a59c9bef97a3e78afcbcc5dd2bd03cad50c1190534ae268f99c7a61ec8ebbb"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    resource: str
    kind: str
    group: str
    basis: str
    purpose: str | None = None
    url: str | None = None
