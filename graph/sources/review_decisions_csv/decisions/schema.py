# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class ReviewDecision:
    __record_set__: ClassVar[str] = "review-decisions.csv#review-decisions"
    __source_digest__: ClassVar[str] = "2220c31b27f5f703fe7a650b56efa6be9a30ae911b1ec4725fbc969297aad2d7"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    review_id: str
    decision: str
