# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import EMAIL, PERSON_NAME


@dataclass(frozen=True, kw_only=True)
class RoleStatementRow:
    __record_set__: ClassVar[str] = "role_statements.jsonl#role_statements"
    __source_digest__: ClassVar[str] = "dad845377065b6f21ae0cc30b4499019acc5b186033c8c34b278b597457416ae"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    person_name: str = source_field("person", term=PERSON_NAME)
    role: str
    role_kind: str
    place: str
    place_kind: str
    work_item: str | None = None
    affiliation: str | None = None
    node: str | None = None
    period: str | None = None
    effort: str | None = None
    funding: str
    email: str | None = source_field("email", term=EMAIL)
