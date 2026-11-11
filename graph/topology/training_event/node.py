from dataclasses import dataclass, field
from typing import ClassVar, NewType


TrainingEventId = NewType("TrainingEventId", str)


@dataclass(frozen=True)
class TrainingEvent:
    """A training event or meeting listed in TeSS, the ELIXIR training portal, including past events. All TeSS events
    are admitted; most are not organised by ELIXIR. Links to Nodes and to ELIXIR groups come from TeSS's own Node
    and collection assignments, but only for the TeSS Node and collection ids whose names the snapshot reveals
    (by a unique match between id counts and TeSS facet counts): absent links do not mean the event has no Node or
    collection, so do not count events per Node from these links alone."""

    schema_id: ClassVar[str] = "atlas:training_event"
    id: TrainingEventId
    tess_id: str = field(metadata={"description": "TeSS identifier."})
    title: str | None = field(metadata={"description": "Title."})
    url: str | None = field(metadata={"description": "Event URL."})
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
    description: str | None = field(metadata={"description": "Description."})
