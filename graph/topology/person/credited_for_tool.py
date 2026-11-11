from dataclasses import dataclass, field
from typing import ClassVar

from ..tool.node import ToolId
from .node import PersonId


@dataclass(frozen=True)
class CreditedForTool:
    """bio.tools credits the person for the tool (developer, maintainer, contact or other)."""

    schema_id: ClassVar[str] = "atlas:credited_for_tool"
    id: str
    source: PersonId
    target: ToolId
    name_as_written: str = field(
        metadata={"description": "The name as bio.tools writes it."}
    )
