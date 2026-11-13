# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import PERSON_NAME


@dataclass(frozen=True, kw_only=True)
class NodePageRoleRow:
    __record_set__: ClassVar[str] = "node_page_roles.jsonl#node_page_roles"
    __source_digest__: ClassVar[str] = "afdd1c7f4d238907f1353563fd93b81431cff5696414a949bdb8bbfd519135e3"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    person_name: str = source_field("person", term=PERSON_NAME)
    role: str
    role_kind: str
    place: str
    place_kind: str
    affiliation: str | None = None
    node: str | None = None
    orcid: str | None = None
