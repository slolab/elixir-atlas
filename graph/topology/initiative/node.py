from dataclasses import dataclass, field
from typing import ClassVar, NewType


InitiativeId = NewType("InitiativeId", str)


@dataclass(frozen=True)
class Initiative:
    """An ELIXIR group or project. family 'group': Communities, Platforms, Focus Groups, working groups, task
    forces and governance or coordinator groups. family 'project': Commissioned Services, Scientific Programme
    projects and work plans, staff exchanges, implementation studies, EU projects (CORDIS) and Node projects.

    One initiative joins the statements of several sources when they share the page URL or a link to it, a
    curated alias, a Scientific Programme code (2024-TECHNOLOGY-Data), the same project acronym (CORDIS), or the
    same name after ignoring case, 'ELIXIR' and the words Community, Platform and Focus Group, or a decision on a
    review_item. A Platform and its 2024-26 Commissioned Service are separate initiatives linked by related_to.
    Other likely matches are open initiative_match review_items. Values each source states are in
    source_statement; start and end here are the own page's values, or else the values the sources agree on
    (within one month), or a decision's. Counts such as the number of Nodes are not stored: count the
    takes_part_in edges."""

    schema_id: ClassVar[str] = "atlas:initiative"
    id: InitiativeId
    name: str = field(
        metadata={
            "description": "The name used on its own ELIXIR page, or else the most frequent name."
        }
    )
    acronym: str | None = field(
        metadata={"description": "Acronym or short name a source gives."}
    )
    kind: str = field(
        metadata={
            "description": "community, platform, focus_group, working_group, task_force, governance_group, commissioned_service, programme_project, staff_exchange, implementation_study, eu_project, node_project, other_project, infrastructure (ELIXIR as a whole, owner of ELIXIR-wide goals and reported results in the Scientific Programme and Annual Report), node_programme (a Node's own plans, e.g. a Node strategy) or node_group (a board, unit or research group named on a Node website, with the Node's name added when the name is generic); the kind most of its sources state. A group or project known only from role statements or as the owner of plan items gets a kind guessed from its name (governance_group for boards and committees, working_group for other groups, other_project for projects)."
        }
    )
    family: str = field(
        metadata={
            "description": "group (community, platform, focus_group, working_group, task_force, governance_group, node_group) or project (every other kind)."
        }
    )
    aliases: list[str] = field(
        metadata={"description": "Every name a source uses for it."}
    )
    pages: list[str] = field(
        metadata={
            "description": "URLs of the web pages that describe it, its own ELIXIR page first."
        }
    )
    identity_basis: list[str] = field(
        metadata={
            "description": "Why its statements were joined: page (the same page URL), link (a listing links to its page), curated_alias (two pages known to describe it), programme_code (the same Scientific Programme code), sub_page (a work-package or project sub-page), work_plan_link (the only project page linking a work plan document), same_name, acronym, decision or single_source."
        }
    )
    start: str | None = field(
        metadata={
            "description": "Start (YYYY, YYYY-MM or YYYY-MM-DD) as its own page states it, or else as all sources agree. A year and a month in that year agree. When sources give dates more than a month apart, a value_conflict review_item lists every value; the value here is then the own page's, a reviewer's decision, or null."
        }
    )
    end: str | None = field(metadata={"description": "End, as for start."})
    status: str | None = field(
        metadata={
            "description": "current, completed or planned, as its own page states; null when not stated."
        }
    )
    summary: str | None = field(
        metadata={
            "description": "What it does and aims at, verbatim from the page that describes it."
        }
    )
    outcomes: list[str] = field(
        metadata={
            "description": "Expected outcomes and objectives the describing page lists."
        }
    )
    contacts: list[str] = field(
        metadata={
            "description": "Contact emails, mailing lists and join links sources give."
        }
    )
    grant_id: str | None = field(
        metadata={"description": "EU grant agreement ID for an EU project."}
    )
    total_cost_eur: float | None = field(
        metadata={"description": "Total cost in euro from CORDIS."}
    )
    eu_contribution_eur: float | None = field(
        metadata={
            "description": "EU contribution in euro from CORDIS; this is the project's grant, not any person's funding."
        }
    )
