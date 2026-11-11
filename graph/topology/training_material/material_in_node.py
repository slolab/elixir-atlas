from dataclasses import dataclass
from typing import ClassVar

from ..elixir_node.node import ElixirNodeId
from .node import TrainingMaterialId


@dataclass(frozen=True)
class MaterialInNode:
    """TeSS assigns the material to this ELIXIR Node."""

    schema_id: ClassVar[str] = "atlas:material_in_node"
    id: str
    source: TrainingMaterialId
    target: ElixirNodeId
