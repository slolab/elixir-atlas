from dataclasses import dataclass
from typing import ClassVar

from ..topic.node import TopicId
from .node import EventId


@dataclass(frozen=True)
class EventTopic:
    """TeSS assigns this EDAM topic to the event."""

    schema_id: ClassVar[str] = "atlas:event_topic"
    id: str
    source: EventId
    target: TopicId
