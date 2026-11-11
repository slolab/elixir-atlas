# This file is yours to edit; biotope rewrites only its IDs and digest when biotope mv moves its file.
# After any other manifest change, review the drift biotope graph check reports, then update __source_digest__.
"""Typed records for one described record set; bindings name its Croissant fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from biotope.graph import source_field

from ....standardization import EMAIL, PERSON_NAME


@dataclass(frozen=True, kw_only=True)
class PerunAccount:
    __record_set__: ClassVar[str] = "export.csv#export"
    __source_digest__: ClassVar[str] = "985fa842385f57a492ac9c01b3bfb2017423a3fc6bce08f32f3a22f47121b87f"
    __missing_values__: ClassVar[frozenset[str]] = frozenset({""})

    type: str
    person_name: str = source_field("fullName", term=PERSON_NAME)
    status: str
    group_status: str = source_field("groupStatus")
    organization: str | None
    email: str = source_field("email", term=EMAIL)
    logins: str
    lifescienceid_username: str = source_field("lifescienceid-username")
