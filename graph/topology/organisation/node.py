from dataclasses import dataclass, field
from typing import ClassVar, NewType


OrganisationId = NewType("OrganisationId", str)


@dataclass(frozen=True)
class Organisation:
    """An organisation: a CORDIS participant of an EU project, or an affiliation that a page or document gives for a
    person. Names are joined only when equal after ignoring case, punctuation and a leading CORDIS country code
    ('CH-SIB' is 'SIB'); other likely matches (an acronym, a shortened name) are open organisation_match review_items."""

    schema_id: ClassVar[str] = "atlas:organisation"
    id: OrganisationId
    name: str = field(
        metadata={
            "description": "The organisation's name as CORDIS gives it, or else the most frequent spelling."
        }
    )
    name_variants: list[str] = field(
        metadata={"description": "Every spelling of the name that a source uses."}
    )
    country: str | None = field(
        metadata={"description": "Country, where CORDIS gives it."}
    )
    activity_type: str | None = field(
        metadata={"description": "CORDIS activity type, e.g. 'Research Organisations'."}
    )
