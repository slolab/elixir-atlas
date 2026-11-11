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
            "description": "Why, one or more of (comma-separated): grant (the record names the project's EU grant), linked (a page about the initiative links to it), deliverable (it is one of the initiative's plan items, see delivers), named (its title names the project's acronym, or a keyword names a Community, Platform, Focus Group or ELIXIR group; the weakest basis)."
        }
    )
