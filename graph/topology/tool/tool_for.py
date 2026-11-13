from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import ToolId


@dataclass(frozen=True)
class ToolFor:
    """bio.tools links the tool to this ELIXIR Community or Platform. basis 'tag': the tool's own elixirCommunity
    or elixirPlatform tag, set by whoever registered the tool. basis 'community_domain': the tool is in a bio.tools
    domain (curated collection) that the group's ELIXIR page links to. Neither is a recommendation by the group;
    see recommends."""

    schema_id: ClassVar[str] = "atlas:tool_for"
    id: str
    source: ToolId
    target: InitiativeId
    basis: str = field(metadata={"description": "tag or community_domain."})
    as_written: str = field(metadata={"description": "The tag as bio.tools writes it, or the domain's name."})
