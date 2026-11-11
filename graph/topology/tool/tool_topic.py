from dataclasses import dataclass
from typing import ClassVar

from ..topic.node import TopicId
from .node import ToolId


@dataclass(frozen=True)
class ToolTopic:
    """bio.tools assigns this EDAM topic to the tool."""

    schema_id: ClassVar[str] = "atlas:tool_topic"
    id: str
    source: ToolId
    target: TopicId
