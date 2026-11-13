from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import TrainingMaterialId


@dataclass(frozen=True)
class MaterialFor:
    """TeSS lists the material in a collection kept by this ELIXIR group. This is the group's own collection, not
    a topic match: materials that only share an EDAM topic with the group have no such edge."""

    schema_id: ClassVar[str] = "atlas:material_for"
    id: str
    source: TrainingMaterialId
    target: InitiativeId
    collection: str = field(metadata={"description": "The TeSS collection's title."})
    source_url: str | None = field(metadata={"description": "The TeSS collection page."})
