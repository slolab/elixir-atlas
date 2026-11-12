from dataclasses import dataclass, field
from typing import ClassVar, NewType


InitiativeId = NewType("InitiativeId", str)


@dataclass(frozen=True)
class Initiative:
    """An ELIXIR group or project. family 'group': Communities, Platforms, Focus Groups, working groups, task
    forces, governance or coordinator groups, Node groups and other groups. family 'project': Commissioned Services
    (including Implementation Studies and Scientific Programme projects and work plans), staff exchanges, EU projects
    (CORDIS) and Node projects.

    The ELIXIR website's directory pages (/communities, /platforms, /focus-groups) define which initiatives are
    ELIXIR Communities, Platforms and Focus Groups and whether each is current or past; no other source can make an
    initiative one of these kinds. A group that has become another group or project has a became edge to it.

    Membership: Community member lists are not public. People appear in a group only when a public page names
    them (leads, liaisons, candidates, plan-item leads and participants, authors), so the people of a group are a
    lower bound, never its membership.

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
            "description": "community, platform and focus_group: only the groups the ELIXIR directory pages list, current or past (Marine Metagenomics is a past Community). working_group, task_force, governance_group, node_group (a board, unit, national community or research group named on a Node website, with the Node's name added when the name is generic), other_group (a group sources call a community or platform that the ELIXIR directory does not list, e.g. an external network), commissioned_service (an ELIXIR-funded project: Commissioned Services, Implementation Studies, and Scientific Programme projects and work plans; the ELIXIR website uses these names for the same kind of project), staff_exchange, eu_project, node_project, other_project, infrastructure (ELIXIR as a whole, owner of ELIXIR-wide goals and reported results in the Scientific Programme and Annual Report), node_programme (a Node's own plans, e.g. a Node strategy) or programme_area (an area of the Scientific Programme, such as Cellular and molecular research, that groups projects; not a project itself, and its related_to links to Communities do not show joint work). Otherwise the kind most of its sources state; a group or project known only from role statements or as the owner of plan items gets a kind guessed from its name."
        }
    )
    family: str = field(
        metadata={
            "description": "group (community, platform, focus_group, working_group, task_force, governance_group, node_group, other_group) or project (every other kind)."
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
            "description": "For Communities, Platforms and Focus Groups: current or past, from the ELIXIR directory pages. For other initiatives: current, completed or planned as its own page states (planned only when it starts after the snapshot, November 2026), null when not stated. A project whose end date has passed without a status update is not marked completed here: compare end with the snapshot date."
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
            "description": "Contact email addresses as its own ELIXIR page shows them to the reader, or else the addresses and mailing lists other sources give. When a page's link sends to another address than it shows, the shown address is kept here and a value_conflict review_item (property contact) names both."
        }
    )
    join_url: str | None = field(
        metadata={"description": "Where its ELIXIR page's 'Join this Community' or 'Join this group' button leads (Life Science Login registration)."}
    )
    joining: str | None = field(
        metadata={"description": "The text its ELIXIR page gives beside the join button, verbatim, with each link's URL in brackets: how to join, approval, onboarding documents and contacts. Null when the page shows only the button: joining is then Life Science Login registration through join_url."}
    )
    leaders: list[str] = field(
        metadata={"description": "Its current leaders as its own page and other sources name them, as 'name (role kinds; Node)': co-leads, leads, chairs, coordinators and liaisons, then work-package leads. Candidates are not included. See involved_in for every person and role."}
    )
    limits: list[str] = field(
        metadata={"description": "What the public sources cannot tell about it, by rule from its kind and data: for groups, member lists are not public; for EU projects, the grant agreement and each partner's effort are not public; for ELIXIR projects, each Node's funding or in-kind status is not stated; whether a joining procedure is given; whether an end date has passed while a page still calls it current. Report the ones that bear on a question."}
    )
    scope: str | None = field(
        metadata={"description": "What it works on, gathered for search: its outcomes, the labels of its goals and objectives, the resources its documents point to and the tools tagged for it. Derived text, not a quote."}
    )
    latest_own_activity: str | None = field(
        metadata={"description": "Date of its latest own dated activity: an output linked by author, title, keyword, link or deliverable, or an ELIXIR website meeting held by the snapshot date. Null when none is dated; that does not prove inactivity."}
    )
    latest_activity: str | None = field(
        metadata={"description": "Date of its latest dated evidence of any kind in recent_activity, including description mentions, announced meetings and project pages that list it."}
    )
    recent_activity: list[str] = field(
        metadata={"description": "Its latest dated public evidence, newest first, at most eight items, each 'date | kind | title | url'. Kinds: 'output (basis)' for an output_of link (author, title, named, linked, deliverable, grant or description; description is a mention only), 'meeting held' or 'meeting announced' for an ELIXIR website event whose title names it (announced: starts after the snapshot date, 2026-11-11), and 'listed on a project page (indirect)' for the first publication date of a project page that names it as related. Own activity is outputs and meetings; a project page listing is indirect. Empty does not prove inactivity: the crawl misses Slack, mailing lists and minutes."}
    )
    period_status: str | None = field(
        metadata={"description": "Whether its period, as start and end give it, has ended, is running or has not started at the snapshot date (2026-11-11): ended, running or not_started; null without an end date. Derived from the dates only: a project whose end has passed is ended here even when a page still calls it current. Use status for Communities, Platforms and Focus Groups."}
    )
    programme: str | None = field(
        metadata={"description": "'2024-28 Scientific Programme' for projects with a page under /how-we-work/scientific-programme on the ELIXIR website; null otherwise."}
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
