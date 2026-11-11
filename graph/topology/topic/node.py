from dataclasses import dataclass, field
from typing import ClassVar, NewType


TopicId = NewType("TopicId", str)


@dataclass(frozen=True)
class Topic:
    """An EDAM topic (http://edamontology.org), from the 296 topics bio.tools and TeSS use. Initiatives and plan
    items get topics assigned by a language model from their own text, so overlaps can be compared with tools and
    training."""

    schema_id: ClassVar[str] = "atlas:topic"
    id: TopicId
    label: str = field(metadata={"description": "EDAM preferred label."})
    uri: str = field(metadata={"description": "EDAM URI."})
