# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class Correction:
    __record_set__: ClassVar[str] = "corrections.csv#corrections"
    __source_digest__: ClassVar[str] = "364045e0c6705a26e40d0c49d1f60a0e90c69cf7254381b13444cf26ababbe41"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    subject: str
    property: str
    action: str
    target: str | None = None
    value: str | None = None
    role: str | None = None
    confirmed_by: str | None = None
    date: str | None = None
    note: str | None = None
