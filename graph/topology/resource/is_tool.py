from dataclasses import dataclass, field
from typing import ClassVar

from ..tool.node import ToolId
from .node import ResourceId


@dataclass(frozen=True)
class IsTool:
    """The resource is this bio.tools entry: its link points to the entry, or its name equals the entry's name or
    bio.tools id after ignoring case and punctuation."""

    schema_id: ClassVar[str] = "atlas:is_tool"
    id: str
    source: ResourceId
    target: ToolId
    basis: str = field(metadata={"description": "url or name."})
