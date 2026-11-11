from dataclasses import dataclass
from typing import ClassVar

from ..topic.node import TopicId
from .node import TrainingMaterialId


@dataclass(frozen=True)
class MaterialTopic:
    """TeSS assigns this EDAM topic to the material."""

    schema_id: ClassVar[str] = "atlas:material_topic"
    id: str
    source: TrainingMaterialId
    target: TopicId
