# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class ElixirPageRow:
    __record_set__: ClassVar[str] = "elixir_pages.jsonl#elixir_pages"
    __source_digest__: ClassVar[str] = "c5570c6ce26a78b15d85500103a3aa94e15d8ff56316ddd5e31b31ac45b6964e"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    published: str | None = None
    modified: str | None = None
    contacts: list[str]
    contact_targets: list[str]
    join_url: str | None = None
    joining: str | None = None
