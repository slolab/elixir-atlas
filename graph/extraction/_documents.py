import re

from ..paths import PROJECT_ROOT

ELIXIR = "data/input/elixir/"

GROUP_PAGES = (
    ELIXIR + "communities-*.html",
    ELIXIR + "focus-groups-*.html",
    ELIXIR + "about-groups*.html",
    ELIXIR + "about-us-governance-*.html",
    ELIXIR + "platforms-????????????.html",
    ELIXIR + "platforms-compute-????????????.html",
    ELIXIR + "platforms-data-????????????.html",
    ELIXIR + "platforms-interoperability-????????????.html",
    ELIXIR + "platforms-tools-????????????.html",
    ELIXIR + "platforms-training-????????????.html",
    ELIXIR + "platforms-training-working-groups-*.html",
)

PROJECT_PAGES = (
    ELIXIR + "internal-projects-commissioned-services-*.html",
    ELIXIR + "internal-projects-staff-exchange-programme-*.html",
    ELIXIR + "how-we-work-scientific-programme-*.html",
    ELIXIR + "about-us-commissioned-services-*.html",
    ELIXIR + "about-us-implementation-studies-*.html",
    ELIXIR + "about-us-how-funded-eu-projects-*.html",
    "data/input/project-pages/*.html",
    "data/input/cordis-*/project-id-*.html",
)

NODE_PROJECT_PAGES = (
    "data/input/node-norway/funding-and-projects*.html",
    "data/input/node-uk/activities*.html",
    "data/input/node-uk/project-*.html",
    "data/input/node-germany/commissioned-services-of-elixir-de-*.html",
    "data/input/node-czech/about-elixir-cz-projects*.html",
    "data/input/node-luxembourg/projects*.html",
    "data/input/node-netherlands/en-projects*.html",
    "data/input/node-portugal/news-*.html",
    "data/input/node-switzerland/activities*.html",
)

NODE_PEOPLE_PAGES = (
    ELIXIR + "about-us-who-we-are-*.html",
    ELIXIR + "about-who-we-are-*.html",
    "data/input/node-czech/about-elixir-cz*.html",
    "data/input/node-finland/*.html",
    "data/input/node-france/en-ifb-elixir-fr*.html",
    "data/input/node-germany/about-*.html",
    "data/input/node-germany/contact-*.html",
    "data/input/node-germany/network-*.html",
    "data/input/node-germany/organisation-*.html",
    "data/input/node-germany/team-*.html",
    "data/input/node-luxembourg/about-node*.html",
    "data/input/node-netherlands/en-*.html",
    "data/input/node-netherlands/elixir-*.html",
    "data/input/node-norway/about*.html",
    "data/input/node-portugal/*.html",
    "data/input/node-spain/about-inb*.html",
    "data/input/node-switzerland/*.html",
    "data/input/node-uk/about*.html",
    "data/input/node-uk/people*.html",
)

WORK_PLANS = (
    "data/input/zenodo/*-files-24-TECHNOLOGY-*.pdf",
    "data/input/zenodo/*-files-Public_Template_24-TECHNOLOGY-*.pdf",
    "data/input/zenodo/*COPY-for-publishing_24-TECHNOLOGY-*.pdf",
    "data/input/zenodo/*-files-24-SCIENCE-BFSP-v2.pdf-*.pdf",
)

HANDBOOKS = (
    "data/input/zenodo-steers/*Project-Handbook*.pdf",
    "data/input/zenodo-converge/cords-8183281-*Project-Handbook-final-version*.pdf",
)

STRATEGY_DOCUMENTS = (
    ELIXIR + "sites-default-files-documents-elixir-programme-24-28-full.pdf-*.pdf",
    ELIXIR + "sites-default-files-documents-elixir-AnnualReport2025.pdf-*.pdf",
    "data/input/f1000/documents-15-1717-pdf-*.pdf",
    "data/input/f1000/articles-11-1265-v2-*.html",
    "data/input/systems-biology/abs-*.html",
    "data/input/systems-biology/pdf-2609.13127-*.pdf",
    "data/input/node-czech/elixir-cz-strategy-elixir-cz-strategy-2026-2030*.html",
)

COMMUNITY_DOCUMENTS = (
    *(f"data/input/f1000/documents-15-{number}-pdf-*.pdf" for number in (1280, 1758, 1506, 1685, 229)),
    "data/input/f1000/articles-14-884-pdf-*.pdf",
    "data/input/f1000/documents-13-80-pdf-*.pdf",
    "data/input/zenodo/api-records-15235047-files-Framework_*.pdf",
    ELIXIR + "services-service-bundles-systems-biology-rare-disease-*.html",
    ELIXIR + "ords-10006029-files-*.pdf",
)

EU_DOCUMENTS = tuple(
    path.relative_to(PROJECT_ROOT).as_posix()
    for path in sorted((PROJECT_ROOT / "data/input/zenodo-steers").glob("*.pdf"))
    if not re.search(r"Handbook|BFSP|ELITMA", path.name)
)

INITIATIVE_DOCUMENTS = GROUP_PAGES + PROJECT_PAGES + NODE_PROJECT_PAGES + WORK_PLANS + HANDBOOKS + STRATEGY_DOCUMENTS + COMMUNITY_DOCUMENTS
ROLE_DOCUMENTS = GROUP_PAGES + PROJECT_PAGES + NODE_PROJECT_PAGES + NODE_PEOPLE_PAGES + WORK_PLANS + HANDBOOKS + COMMUNITY_DOCUMENTS + EU_DOCUMENTS
PLAN_LINK_DOCUMENTS = PROJECT_PAGES + WORK_PLANS + HANDBOOKS + COMMUNITY_DOCUMENTS + EU_DOCUMENTS
PLAN_DOCUMENTS = GROUP_PAGES + PROJECT_PAGES + NODE_PROJECT_PAGES + WORK_PLANS + HANDBOOKS + STRATEGY_DOCUMENTS + COMMUNITY_DOCUMENTS + EU_DOCUMENTS

DIRECTORY_PAGES = (
    ELIXIR + "communities-????????????.html",
    ELIXIR + "focus-groups-????????????.html",
    ELIXIR + "platforms-????????????.html",
    ELIXIR + "communities-marine-metagenomics-*.html",
)
ELIXIR_PAGES = tuple(pattern for pattern in GROUP_PAGES + PROJECT_PAGES if pattern.startswith((ELIXIR, "data/input/project-pages/")))
ELECTION_PAGES = (ELIXIR + "communities-co-lead-elections-*.html",)
EVENT_PAGES = (ELIXIR + "events-*.html",)
RECOMMENDATION_DOCUMENTS = (
    ELIXIR + "communities-*-????????????.html",
    "data/input/f1000/articles-11-1265-v2-*.html",
    "data/input/f1000/documents-15-1717-pdf-*.pdf",
    "data/input/systems-biology/pdf-2609.13127-*.pdf",
    *(f"data/input/f1000/documents-15-{number}-pdf-*.pdf" for number in (1280, 1758, 1506, 1685, 229)),
    ELIXIR + "ords-10006029-files-*.pdf",
)
CORDIS_DOCUMENTS = (
    "data/input/cordis-*/project-id-?????????-????????????-????????????.html",
    "data/input/cordis-*/project-id-??????-????????????-????????????.html",
)
