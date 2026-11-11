from dataclasses import dataclass, field
from typing import ClassVar

from ..elixir_node.node import ElixirNodeId
from .node import ToolId


@dataclass(frozen=True)
class ToolInNode:
    """bio.tools tags the tool with this ELIXIR Node."""

    schema_id: ClassVar[str] = "atlas:tool_in_node"
    id: str
    source: ToolId
    target: ElixirNodeId
    as_written: str = field(metadata={"description": "The tag as bio.tools writes it."})
