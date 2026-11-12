from dataclasses import dataclass, field
from typing import ClassVar

from .node import InitiativeId


@dataclass(frozen=True)
class SharesWorkWith:
    """Two groups (Communities, Platforms, Focus Groups and other groups) that share a piece of work, one edge
    per shared item, stored in both directions. via 'project': a project names both (related_to); 'output': an
    output is linked to both by author, title, keyword, link or deliverable; 'tool': bio.tools tags a tool for
    both; 'leader': one person holds a leadership role in both; 'resource': both groups' documents point to the
    same resource. Programme areas and ELIXIR-wide projects with more than eight groups are left out: they group
    work rather than share it. Count distinct items per pair for the strength of an overlap."""

    schema_id: ClassVar[str] = "atlas:shares_work_with"
    id: str
    source: InitiativeId
    target: InitiativeId
    via: str = field(metadata={"description": "project, output, tool, leader or resource."})
    item: str = field(metadata={"description": "The shared item's name or title."})
    item_id: str = field(metadata={"description": "The shared item's record id (initiative, output, tool, person or resource)."})
    source_url: str | None = field(metadata={"description": "A page or document that states one of the two links, where one is known."})
