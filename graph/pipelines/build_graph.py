"""Register the pipeline: its scope, sources, mappings and scientific policies."""

from biotope.graph import Pipeline

from ..mappings import MAPPINGS
from ..paths import GRAPH_ROOT
from ..sources import EXCLUDED_SOURCES, SOURCES
from ..sources.inventory import INVENTORY
from ..standardization import TERMS
from ..topology import TOPOLOGY
from .compose import run


PIPELINE = Pipeline(
    name="elixir-atlas",
    topology=TOPOLOGY,
    sources=SOURCES,
    mappings=MAPPINGS,
    run=run,
    scope=(
        "The ELIXIR Atlas: ELIXIR groups (Communities, Platforms and Focus Groups as the ELIXIR directory pages list "
        "them, current or past, plus working groups, task forces, governance, Node and other groups) and projects "
        "(Commissioned Services including Scientific Programme projects and Implementation Studies, staff exchanges, "
        "EU projects, Node projects), the people, Nodes and organisations involved, their roles, plan items, outputs, "
        "tools, resources groups recommend, events and training, from the 2026-11 snapshot of the ELIXIR, Node, "
        "CORDIS, Zenodo, F1000, bio.tools, TeSS, Europe PMC and Perun sources. The snapshot is a crawl of public pages "
        "and catalogues, not a complete record: a group or person absent from it, or with no recent page, is not "
        "shown to be inactive. Community member lists are not public, so the people of a group are those public "
        "pages name. One source_statement per page or document about an initiative; one holds_role edge per stated "
        "role; values the sources disagree on are listed as review_items, and an initiative keeps only its own page's "
        "value or a reviewer's decision."
    ),
    code_paths=tuple(
        GRAPH_ROOT / path
        for path in (
            "__init__.py",
            "paths.py",
            "standardization.py",
            "alignment",
            "extraction",
            "sources",
            "topology",
            "mappings",
            "pipelines",
        )
    ),
    terms=TERMS,
    source_inventory=INVENTORY,
    excluded_sources=EXCLUDED_SOURCES,
    policies={
        "biotools_without_elixir_tag": (
            "A bio.tools entry with no ELIXIR Node, Platform or Community tag, in none of the bio.tools domains a "
            "Community page links, crediting no person whom a role statement, plan item or election page names, and "
            "matching no tool or database a group recommends, is outside the atlas."
        ),
        "superseded_by_page_parser": (
            "A role statement the language model read from a page whose structure a code reader parses (the co-lead "
            "election page); the parsed records replace it."
        ),
        "duplicate_record": (
            "The record repeats another of the same source: a second version of an F1000 article with the same DOI, "
            "an event listed on the events page and on its own page, or a directory entry on two listing pages. The "
            "first is kept and its links include those of the repeats."
        ),
        "recommendation_group_unresolved": (
            "The recommendation names a group that matches no Community, Platform or Focus Group of the ELIXIR "
            "directory."
        ),
        "plan_link_unresolved": (
            "The plan link names a project or group that matches no initiative, or links an initiative to itself."
        ),
        "role_holder_not_a_person": "The role holder a source names is a group, organisation, Node or placeholder, not a person.",
        "role_place_unresolved": "The place of a role is neither a known group, project, Node or organisation nor named clearly enough to add one.",
        "plan_owner_unresolved": "The plan item names an owner that no initiative matches, and its document describes none.",
        "superseded_snapshot": "A newer snapshot of the same page (same URL) exists in the scraping index; only the newest is read.",
        "perun_account_not_a_person": "The Perun account name is not a person's name (a service or test account).",
    },
    settings={},
)
