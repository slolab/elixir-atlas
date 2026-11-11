# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class TessFacet:
    __record_set__: ClassVar[str] = "tess_facets.jsonl#tess_facets"
    __source_digest__: ClassVar[str] = "2ac203f32d85c49dba861e22813f45f47702c434f5888cf491dd9ebf05dc1086"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    catalogue: str
    count: int
    facet: str
    source_path: str
    value: str
