from dataclasses import dataclass, field
from typing import ClassVar

from ..output.node import OutputId
from .node import PersonId


@dataclass(frozen=True)
class Authored:
    """The person is listed on the output: as an author (creator) or as a Zenodo contributor; see role."""

    schema_id: ClassVar[str] = "atlas:authored"
    id: str
    source: PersonId
    target: OutputId
    position: int = field(
        metadata={"description": "1-based position in the author list."}
    )
    name_as_written: str = field(
        metadata={"description": "The name as the output lists it."}
    )
    affiliation: str | None = field(
        metadata={"description": "Affiliation the output gives for this author."}
    )
    role: str = field(
        metadata={
            "description": "creator (an author of the record) or contributor (a Zenodo contributor such as a supervisor, editor, project member or other; not an author). Contributors follow the creators in position."
        }
    )
