from dataclasses import dataclass, field
from typing import ClassVar, NewType


OutputId = NewType("OutputId", str)


@dataclass(frozen=True)
class Output:
    """A published output: a Zenodo record (deliverables, work plans, reports, slides, posters) found from the
    ELIXIR site, the ELIXIR, STEERS, CONVERGE and EXCELERATE Zenodo searches and Node pages, or an item of the
    F1000Research ELIXIR Gateway (article, document, poster, slides)."""

    schema_id: ClassVar[str] = "atlas:output"
    id: OutputId
    kind: str = field(
        metadata={
            "description": "zenodo_record, or the F1000 item kind: article, document, poster or slide."
        }
    )
    title: str | None = field(metadata={"description": "Title."})
    date: str | None = field(metadata={"description": "Publication date."})
    doi: str | None = field(metadata={"description": "DOI without resolver prefix."})
    url: str | None = field(metadata={"description": "Landing page URL."})
    resource_type: str | None = field(metadata={"description": "Zenodo resource type."})
    version: str | None = field(
        metadata={"description": "Version as the record gives it."}
    )
    keywords: list[str] = field(metadata={"description": "Keywords or subjects."})
    communities: list[str] = field(
        metadata={"description": "Zenodo community identifiers."}
    )
    grants: list[str] = field(
        metadata={"description": "EU grant codes the record names."}
    )
    authors: list[str] = field(
        metadata={"description": "Authors (Zenodo creators) as the record writes them, in order."}
    )
    contributors: list[str] = field(
        metadata={"description": "Zenodo contributors (supervisors, editors, project members, others), who are not authors; empty for other sources."}
    )
    description: str | None = field(
        metadata={"description": "Abstract or description."}
    )
