from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import TrainingMaterialId


@dataclass(frozen=True)
class MaterialFor:
    """TeSS lists the material in a collection kept by this ELIXIR group."""

    schema_id: ClassVar[str] = "atlas:material_for"
    id: str
    source: TrainingMaterialId
    target: InitiativeId
    collection: str = field(metadata={"description": "The TeSS collection's title."})
