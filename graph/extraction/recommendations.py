from dataclasses import dataclass, field
from typing import ClassVar, Literal

from ._llm import MODEL, LlmExtractor


@dataclass(frozen=True, kw_only=True)
class Recommendation:
    """A tool, database, standard, guideline, practice or training resource that an ELIXIR Community page or a
    Community paper (white paper, meeting report, recommendations paper, service bundle) recommends, endorses,
    develops or lists as a resource for its field. One record per resource and group. Leave out resources only
    cited as related work or background, used once as an example, or reachable only through a catalogue the
    document links to without naming the resource."""

    __record_key__: ClassVar[tuple[str, ...]] = ("resource", "group")

    resource: str = field(
        metadata={"description": "The resource's name as written, e.g. 'MEMOTE', 'SBML', 'standard-GEM'."}
    )
    kind: Literal["tool", "database", "standard", "guideline", "practice", "training", "document"] = field(
        metadata={
            "description": "tool is software; database a data resource or repository; standard a format, "
            "ontology or minimum-information checklist; guideline a set of recommendations or a scorecard; "
            "practice a way of working; training a course or material; document a paper or report to read."
        }
    )
    group: str = field(
        metadata={"description": "The ELIXIR Community or group whose page or paper names the resource, as written."}
    )
    basis: Literal["recommends", "develops", "lists"] = field(
        metadata={
            "description": "recommends when the document recommends, endorses or calls it a community standard or "
            "best practice; develops when the group or its members develop or maintain it; lists when it is only "
            "listed among the group's resources."
        }
    )
    purpose: str | None = field(
        metadata={
            "description": "What the document says the resource is for, as a short phrase close to its wording, "
            "e.g. 'testing the quality of genome-scale metabolic models'."
        }
    )
    url: str | None = field(metadata={"description": "The link the document gives for the resource."})


class RecommendationReader(LlmExtractor):
    name = "recommendation-reader"
    version = "1"
    settings = {"model": MODEL, "reasoning": "low"}
    instructions = (
        "Read lists of resources, tables of tools and standards, and recommendation sections. A numbered "
        "recommendation that names no resource is a practice: name it by its short title. A resource a group "
        "member develops counts as develops only when the document says so. Give the group by its ELIXIR name, such "
        "as 'Systems Biology Community', without words such as 'European' or 'ELIXIR'."
    )
