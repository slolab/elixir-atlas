# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import EDAM_TOPIC_URIS, ORCIDS, PERSON_NAMES


@dataclass(frozen=True, kw_only=True)
class BiotoolsTool:
    __record_set__: ClassVar[str] = "biotools.jsonl#biotools"
    __source_digest__: ClassVar[str] = "3fa12c575ef7e4cd7e0a308391ae506309fadec13af1c327c631f0de70c4a804"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    addition_date: str | None
    biotools_id: str
    collections: list[str]
    credit_emails: list[str]
    person_names: list[str] = source_field("credit_names", term=PERSON_NAMES)
    orcids: list[str] = source_field("credit_orcids", term=ORCIDS)
    credit_types: list[str]
    description: str | None
    elixir_communities: list[str]
    elixir_nodes: list[str]
    elixir_platforms: list[str]
    homepage: str | None
    last_update: str | None
    name: str | None
    publication_dois: list[str]
    source_path: str
    tool_types: list[str]
    topic_labels: list[str]
    edam_topic_uris: list[str] = source_field("topic_uris", term=EDAM_TOPIC_URIS)
