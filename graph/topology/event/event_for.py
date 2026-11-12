from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import EventId


@dataclass(frozen=True)
class EventFor:
    """The event belongs to this ELIXIR group: TeSS lists it in a collection the group keeps (basis tess_collection),
    or the event's title on the ELIXIR website names the group (basis title)."""

    schema_id: ClassVar[str] = "atlas:event_for"
    id: str
    source: EventId
    target: InitiativeId
    basis: str = field(metadata={"description": "tess_collection or title."})
    collection: str | None = field(metadata={"description": "The TeSS collection's title, for basis tess_collection."})
    source_url: str | None = field(
        metadata={"description": "The TeSS collection page, or the ELIXIR events page that lists the event."}
    )
