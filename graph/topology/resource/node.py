from dataclasses import dataclass, field
from typing import ClassVar, NewType


ResourceId = NewType("ResourceId", str)


@dataclass(frozen=True)
class Resource:
    """A tool, database, standard, guideline, practice, training resource or document that an ELIXIR group
    recommends, develops or lists (see recommends). One resource per name after ignoring case and punctuation;
    names are not merged with bio.tools entries except through is_tool."""

    schema_id: ClassVar[str] = "atlas:resource"
    id: ResourceId
    name: str = field(metadata={"description": "The name most documents use."})
    kind: str = field(
        metadata={
            "description": "tool, database, standard (a format, ontology or minimum-information checklist), guideline (recommendations or a scorecard), practice (a way of working), training or document; the kind most documents give."
        }
    )
    url: str | None = field(metadata={"description": "The link a document gives for it."})
