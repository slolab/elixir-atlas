from dataclasses import dataclass, field
from typing import ClassVar, NewType


ToolId = NewType("ToolId", str)


@dataclass(frozen=True)
class Tool:
    """A software tool, database or service registered in bio.tools that carries at least one ELIXIR Node,
    Platform or Community tag. Tools without ELIXIR tags are not admitted (policy biotools_without_elixir_tag), and
    bio.tools collections are not Communities (a 'Plant Systems Biology' collection is not the Systems Biology
    Community)."""

    schema_id: ClassVar[str] = "atlas:tool"
    id: ToolId
    biotools_id: str = field(metadata={"description": "bio.tools identifier."})
    name: str | None = field(metadata={"description": "Tool name."})
    description: str | None = field(metadata={"description": "bio.tools description."})
    homepage: str | None = field(metadata={"description": "Homepage URL."})
    url: str = field(metadata={"description": "bio.tools page URL."})
    tool_types: list[str] = field(metadata={"description": "bio.tools tool types."})
    elixir_nodes: list[str] = field(
        metadata={"description": "ELIXIR Node tags as bio.tools writes them."}
    )
    elixir_platforms: list[str] = field(
        metadata={"description": "ELIXIR Platform tags as bio.tools writes them."}
    )
    elixir_communities: list[str] = field(
        metadata={"description": "ELIXIR Community tags as bio.tools writes them."}
    )
    collections: list[str] = field(
        metadata={"description": "bio.tools collections; not ELIXIR groups."}
    )
    topics: list[str] = field(metadata={"description": "EDAM topic labels."})
    recommended_by: list[str] = field(
        metadata={"description": "Groups whose own page or paper points to this tool (recommends with is_tool), as 'group (basis)'. Empty means no group document was found naming it: a tool_for tag or domain listing alone is a catalogue entry, not a recommendation."}
    )
    last_update: str | None = field(
        metadata={"description": "When the bio.tools entry was last updated."}
    )
