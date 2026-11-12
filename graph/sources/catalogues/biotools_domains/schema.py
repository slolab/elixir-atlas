# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class BiotoolsDomain:
    __record_set__: ClassVar[str] = "biotools_domains.jsonl#biotools_domains"
    __source_digest__: ClassVar[str] = "ffe4276467b64f9eba1396c7db644ced0bec44f329555b0b69fd91a4e644a878"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    biotools_id: str
    domain: str
    source_path: str
