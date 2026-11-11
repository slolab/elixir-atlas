from dataclasses import dataclass, field
from typing import ClassVar, Literal

from ._llm import MODEL, LlmExtractor

InitiativeKind = Literal[
    "community",
    "platform",
    "focus_group",
    "working_group",
    "task_force",
    "governance_group",
    "commissioned_service",
    "programme_project",
    "staff_exchange",
    "implementation_study",
    "eu_project",
    "node_project",
    "other_project",
]


@dataclass(frozen=True, kw_only=True)
class InitiativeStatement:
    """What one ELIXIR web page or document states about one ELIXIR group or project. Groups are Communities,
    Platforms, Focus Groups, working groups, task forces and governance or coordinator groups; projects are
    Commissioned Services, projects and work plans of the 2024-28 Scientific Programme, staff exchanges,
    implementation studies, EU-funded projects and Node projects. One record per group or project that the
    document describes, or lists with at least a date, a Node, a lead, a link or an aim. Leave out groups and
    projects only named in passing or in menus, and organisations or networks outside ELIXIR."""

    __record_key__: ClassVar[tuple[str, ...]] = ("name",)

    name: str = field(
        metadata={
            "description": "The group's or project's name exactly as this document writes it, including any "
            "years in it, e.g. 'ELIXIR Compute Platform (2024-26)'."
        }
    )
    acronym: str | None = field(
        metadata={"description": "Short name or acronym the document gives, e.g. 'DBTLHub', 'ELIXIR-STEERS'."}
    )
    kind: InitiativeKind = field(
        metadata={
            "description": "What the document says it is. governance_group covers boards, committees and "
            "coordinator groups; programme_project covers projects and work plans of the 2024-28 Scientific "
            "Programme that are not called Commissioned Services; node_project is a project run by an ELIXIR Node."
        }
    )
    coverage: Literal["described", "listed"] = field(
        metadata={
            "description": "described when the document is mainly about this group or project; listed when "
            "it appears in a list or overview."
        }
    )
    status: Literal["current", "completed", "planned", "not_stated"] = field(
        metadata={"description": "Status as the document states it; not_stated when it does not."}
    )
    period: str | None = field(
        metadata={
            "description": "Duration or period exactly as written, e.g. 'January 2025 to January 2026', '2024-26'."
        }
    )
    start: str | None = field(
        metadata={"description": "Start of the stated period as YYYY, YYYY-MM or YYYY-MM-DD."}
    )
    end: str | None = field(metadata={"description": "End of the stated period as YYYY, YYYY-MM or YYYY-MM-DD."})
    summary: str | None = field(
        metadata={
            "description": "The document's own description of what the group or project does and aims at, "
            "copied verbatim, up to about 150 words."
        }
    )
    outcomes: list[str] = field(
        metadata={
            "description": "Each expected outcome or objective the document lists, as a short phrase close to "
            "its wording."
        }
    )
    nodes: list[str] = field(
        metadata={
            "description": "ELIXIR Nodes the document states take part in it, as written, e.g. 'ELIXIR Portugal'. "
            "Not the Node of a named person unless the document lists that Node as taking part."
        }
    )
    leads: list[str] = field(
        metadata={
            "description": "People, organisations or Nodes the document states lead or coordinate it, as written."
        }
    )
    related: list[str] = field(
        metadata={
            "description": "Other ELIXIR groups, Platforms, projects or programme tiers the document states are "
            "involved in, linked to, or the parent of it, as written."
        }
    )
    topics: list[str] = field(
        metadata={
            "description": "EDAM topics, only from the list in the instructions, that the document's description "
            "of the group or project directly supports; at most 6."
        }
    )
    contacts: list[str] = field(
        metadata={
            "description": "Contact email addresses, mailing lists and join or subscription links the document "
            "gives for it."
        }
    )
    links: list[str] = field(
        metadata={
            "description": "URLs the document gives for its outputs and resources: work plans, deliverables, "
            "reports, publications, Zenodo or GitHub records, websites."
        }
    )
    funding: str | None = field(
        metadata={
            "description": "Any statement about how it is funded, or the amount, as written, e.g. "
            "'EU contribution € 3 200 000,00'."
        }
    )


class InitiativeReader(LlmExtractor):
    name = "initiative-reader"
    version = "1"
    settings = {"model": MODEL, "reasoning": "low"}
    uses_topics = True
    instructions = (
        "A page about one group or project gives one 'described' record, plus 'listed' records for other ELIXIR "
        "groups or projects it lists with details (dates, Nodes, leads, links or aims). Overview and listing "
        "pages give one 'listed' record per entry. Keep each entry's name as this page writes it, even when you "
        "think another page names it differently. A Platform's, Community's or tier's funded work plan for a "
        "period, such as 'ELIXIR Compute Platform (2024-26)' on a Commissioned Services page, is a "
        "commissioned_service or programme_project, not the Platform or Community itself."
    )
