from dataclasses import dataclass, field
from typing import ClassVar, NewType


TrainingMaterialId = NewType("TrainingMaterialId", str)


@dataclass(frozen=True)
class TrainingMaterial:
    """A training material listed in TeSS. All TeSS materials are admitted; links to Nodes and ELIXIR groups come
    from TeSS's own Node and collection assignments, only for ids whose names the snapshot reveals (see
    event)."""

    schema_id: ClassVar[str] = "atlas:training_material"
    id: TrainingMaterialId
    tess_id: str = field(metadata={"description": "TeSS identifier."})
    title: str | None = field(metadata={"description": "Title."})
    url: str | None = field(metadata={"description": "The material's entry in TeSS."})
    provider_url: str | None = field(metadata={"description": "The material's own page that TeSS links to."})
    doi: str | None = field(metadata={"description": "DOI."})
    authors: list[str] = field(metadata={"description": "Authors as TeSS lists them."})
    resource_types: list[str] = field(metadata={"description": "Resource types."})
    date_published: str | None = field(
        metadata={"description": "Publication or creation date."}
    )
    keywords: list[str] = field(metadata={"description": "Keywords."})
    topics: list[str] = field(metadata={"description": "EDAM topic labels."})
    content_provider: str | None = field(
        metadata={"description": "TeSS content provider."}
    )
    collections: list[str] = field(
        metadata={"description": "Every TeSS collection it belongs to whose name the snapshot reveals, such as an ELIXIR Community's collection. Empty with collections_unnamed 0 means it is in no TeSS collection: listed in TeSS only."}
    )
    collections_unnamed: int = field(
        metadata={"description": "How many of its TeSS collections could not be named from the snapshot; when above 0, collections is incomplete."}
    )
    description: str | None = field(metadata={"description": "Description."})
