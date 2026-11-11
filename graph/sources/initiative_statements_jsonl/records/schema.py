# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class InitiativeStatementRow:
    __record_set__: ClassVar[str] = "initiative_statements.jsonl#initiative_statements"
    __source_digest__: ClassVar[str] = "b02e86f1bd4c352f5bf16e0e74dc899696db8afc1f39d5f56c0fdac59bd8962a"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    name: str
    acronym: str | None = None
    kind: str
    coverage: str
    status: str
    period: str | None = None
    start: str | None = None
    end: str | None = None
    summary: str | None = None
    outcomes: list[str]
    nodes: list[str]
    leads: list[str]
    related: list[str]
    topics: list[str]
    contacts: list[str]
    links: list[str]
    funding: str | None = None
