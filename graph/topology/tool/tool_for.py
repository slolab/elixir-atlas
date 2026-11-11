from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import ToolId


@dataclass(frozen=True)
class ToolFor:
    """bio.tools tags the tool with this ELIXIR Community or Platform."""

    schema_id: ClassVar[str] = "atlas:tool_for"
    id: str
    source: ToolId
    target: InitiativeId
    as_written: str = field(metadata={"description": "The tag as bio.tools writes it."})
