from dataclasses import dataclass
from typing import ClassVar

from ..elixir_node.node import ElixirNodeId
from .node import EventId


@dataclass(frozen=True)
class EventInNode:
    """TeSS assigns the event to this ELIXIR Node."""

    schema_id: ClassVar[str] = "atlas:event_in_node"
    id: str
    source: EventId
    target: ElixirNodeId
