# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class ElixirEventRow:
    __record_set__: ClassVar[str] = "elixir_events.jsonl#elixir_events"
    __source_digest__: ClassVar[str] = "a9ddffa030945ffad69f8bf87d4baf240d12b35f3a7c4315c67545be1fc82d14"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    title: str
    start: str | None = None
    end: str | None = None
    url: str | None = None
