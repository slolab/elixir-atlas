# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class CordisParticipantRow:
    __record_set__: ClassVar[str] = "cordis_participants.jsonl#cordis_participants"
    __source_digest__: ClassVar[str] = "72a65c63f4a6ae6155c33168ce17c5d245cc1829b4681d1d669975b40997c4ca"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    id: str
    document: str
    grant_id: str
    organisation: str
    country: str | None = None
    participation: str
    participation_ended: bool
    net_eu_contribution_eur: float | None = None
    total_cost_eur: float | None = None
    activity_type: str | None = None
