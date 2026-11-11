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
        "The ELIXIR Atlas: ELIXIR groups (Communities, Platforms, Focus Groups, working groups, task forces, "
        "governance groups) and projects (Commissioned Services, Scientific Programme work plans, staff exchanges, "
        "implementation studies, EU projects, Node projects), the people, Nodes and organisations involved, their "
        "roles, plan items, outputs, tools and training, from the 2026-11 snapshot of the ELIXIR, Node, CORDIS, "
        "Zenodo, F1000, bio.tools, TeSS, Europe PMC and Perun sources. One source_statement per page or document "
        "about an initiative; one holds_role edge per stated role; values the sources disagree on are listed as "
        "review_items, and an initiative keeps only its own page's value or a reviewer's decision. bio.tools entries without an ELIXIR tag are excluded."
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
        "biotools_without_elixir_tag": "A bio.tools entry with no ELIXIR Node, Platform or Community tag is outside the atlas.",
        "role_holder_not_a_person": "The role holder a source names is a group, organisation, Node or placeholder, not a person.",
        "role_place_unresolved": "The place of a role is neither a known group, project, Node or organisation nor named clearly enough to add one.",
        "plan_owner_unresolved": "The plan item names an owner that no initiative matches, and its document describes none.",
        "superseded_snapshot": "A newer snapshot of the same page (same URL) exists in the scraping index; only the newest is read.",
        "perun_account_not_a_person": "The Perun account name is not a person's name (a service or test account).",
    },
    settings={},
)
