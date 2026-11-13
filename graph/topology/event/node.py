from dataclasses import dataclass, field
from typing import ClassVar, NewType


EventId = NewType("EventId", str)


@dataclass(frozen=True)
class Event:
    """An event that TeSS (the ELIXIR training portal) or the ELIXIR website lists, including past events.
    listed_in 'tess': every TeSS event is admitted, most are not organised by ELIXIR; links to Nodes and ELIXIR
    groups come from TeSS's own Node and collection assignments, only for the TeSS ids whose names the snapshot
    reveals (by a unique match between id counts and TeSS facet counts), so absent links do not mean the event has
    no Node or collection. listed_in 'elixir_website': an event on the ELIXIR events listing or an ELIXIR event
    page, such as a Community meeting, All Hands, a Board meeting or a co-located Platform meeting; its group links
    come from the group's name in the title. A dated event is evidence of a group's activity at that date only when
    an event_for edge links them."""

    schema_id: ClassVar[str] = "atlas:event"
    id: EventId
    listed_in: str = field(metadata={"description": "tess or elixir_website."})
    tess_id: str | None = field(metadata={"description": "TeSS identifier; null for ELIXIR website events."})
    title: str | None = field(metadata={"description": "Title."})
    url: str | None = field(
        metadata={"description": "The event's entry in TeSS, or its ELIXIR website page."}
    )
    provider_url: str | None = field(
        metadata={"description": "The organiser's own event page that TeSS links to."}
    )
    start: str | None = field(metadata={"description": "Start (ISO 8601)."})
    end: str | None = field(metadata={"description": "End (ISO 8601)."})
    event_types: list[str] = field(
        metadata={"description": "TeSS event types, e.g. workshops_and_courses."}
    )
    online: bool | None = field(metadata={"description": "True for online events."})
    city: str | None = field(metadata={"description": "City."})
    country: str | None = field(metadata={"description": "Country."})
    organizer: str | None = field(
        metadata={"description": "Organiser as TeSS gives it."}
    )
    host_institutions: list[str] = field(metadata={"description": "Host institutions."})
    keywords: list[str] = field(metadata={"description": "Keywords."})
    topics: list[str] = field(metadata={"description": "EDAM topic labels."})
    content_provider: str | None = field(
        metadata={
            "description": "TeSS content provider, where its name could be identified."
        }
    )
    collections: list[str] = field(
        metadata={"description": "Every TeSS collection it belongs to whose name the snapshot reveals, such as an ELIXIR Community's collection. Empty with collections_unnamed 0 means it is in no TeSS collection: listed in TeSS only."}
    )
    collections_unnamed: int = field(
        metadata={"description": "How many of its TeSS collections could not be named from the snapshot; when above 0, collections is incomplete."}
    )
    description: str | None = field(metadata={"description": "Description."})
