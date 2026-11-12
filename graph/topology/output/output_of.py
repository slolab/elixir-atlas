from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import OutputId


@dataclass(frozen=True)
class OutputOf:
    """The output belongs to this group or project."""

    schema_id: ClassVar[str] = "atlas:output_of"
    id: str
    source: OutputId
    target: InitiativeId
    basis: str = field(
        metadata={
            "description": "Why, one or more of (comma-separated): grant (the record names the project's EU grant and is dated no later than the year after the project ended; later records that only acknowledge the grant are not linked), linked (a page about the initiative links to it), deliverable (it is one of the initiative's plan items, see delivers), series (its title starts like other outputs of one work-package series, such as 'BFSP CoS | WP3 |', and those outputs belong to this project), author (the group itself is listed as an author or creator), title (its title names the Community, Platform, Focus Group or project), named (a keyword names the group or the project's acronym), description (its description names the Community, Platform or Focus Group; the weakest basis: a mention, not authorship)."
        }
    )
