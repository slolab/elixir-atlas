from dataclasses import dataclass
from typing import ClassVar

from ..topic.node import TopicId
from .node import PlanItemId


@dataclass(frozen=True)
class PlanItemTopic:
    """An EDAM topic a language model assigned from the plan item's title or description."""

    schema_id: ClassVar[str] = "atlas:plan_item_topic"
    id: str
    source: PlanItemId
    target: TopicId
