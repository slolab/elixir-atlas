from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import TrainingEventId


@dataclass(frozen=True)
class EventFor:
    """TeSS lists the event in a collection kept by this ELIXIR group."""

    schema_id: ClassVar[str] = "atlas:event_for"
    id: str
    source: TrainingEventId
    target: InitiativeId
    collection: str = field(metadata={"description": "The TeSS collection's title."})
