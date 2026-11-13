from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlencode

from discovery import DOCUMENTS, biotools, tess, website, f1000, zenodo, files, europepmc


@dataclass(frozen=True)
class Source:
    urls: tuple[str, ...]
    discover: Callable = website
    sections: tuple[int, ...] = ()
    deferred: str = ""
    formats: frozenset[str] = frozenset(DOCUMENTS)
    browser: bool = False
    paths: tuple[str, ...] = ("/",)
    query_keys: tuple[str, ...] = ("page", "paged", "start", "limitstart")
    listing_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    access: str = "public"
    render_waits: dict[str, str] = field(default_factory=dict)


EU_PROJECTS = {"steers": "101131096", "converge": "871075", "excelerate": "676559"}
PROJECT_DOCUMENTS = frozenset(DOCUMENTS - {".csv", ".tsv", ".json", ".xml"})


SOURCES = {
    "biotools": Source(("https://bio.tools/api/t/?format=json&per_page=100&sort=additionDate&ord=asc",), discover=biotools, sections=(10,)),
    "biotools-domains": Source(tuple(
        f"https://bio.tools/api/t/?format=json&domain={domain}&per_page=100"
        for domain in ("constraint-based-modelling", "qual-logical-models", "rule-based-modelling")
    ), discover=biotools, sections=(10,)),
    "tess-events": Source((
        "https://tess.elixir-europe.org/events.json_api?include_expired=true&page_size=100",
    ), discover=tess, sections=(11,)),
    "tess-materials": Source((
        "https://tess.elixir-europe.org/materials.json_api?page_size=100",
    ), discover=tess, sections=(11,)),
    "elixir": Source(tuple("https://elixir-europe.org" + path for path in (
        "/", "/platforms", "/communities", "/focus-groups", "/about-us/who-we-are/nodes",
        "/how-we-work/scientific-programme",
        "/sites/default/files/documents/elixir-programme-24-28-full.pdf", "/internal-projects/commissioned-services-list",
        "/news", "/events",
        "/events/demystifying-elixir-everything-you-ever-wanted-know-and-more",
    )) + ("https://drive.google.com/file/d/1rlKh7XPXMnjyNyGGRcdg07ojzFZoOVWR/view",),
       sections=(1, 2, 5, 7), browser=True, listing_paths=("/news", "/events"),
       exclude_paths=("/news/", "/users/", "/jobs", "/vacancies", "/about-us/vacancies")),
    "node-uk": Source(("https://elixiruknode.org/",), sections=(3,),
                      listing_paths=("/news", "/news-and-stories", "/events"),
                      exclude_paths=("/news/", "/news-and-stories/", "/articles/", "/uncategorized/", "/jobs", "/vacancies", "/category/", "/tag/")),
    "node-germany": Source(("https://www.denbi.de/",), sections=(3,),
                           listing_paths=("/news", "/news1", "/de-nbi-events", "/training"),
                           exclude_paths=("/news1/", "/news-archive", "/download", "/images/Downloads/Newsletter/", "/jobs", "/de-nbi-jobs-portal", "/elixir-jobs-portal",
                                          "/de-nbi-events-archive", "/training-archive-sorted-according-by-date")),
    "node-spain": Source(("https://inb-elixir.es/",), sections=(3,),
                         listing_paths=("/news", "/events"),
                         exclude_paths=("/news/", "/jobs", "/user/", "/taxonomy/")),
    "elitma": Source(("https://elixir-europe-training.github.io/ELIXIR-ELITMa/",),
                     sections=(6,), paths=("/ELIXIR-ELITMa/",)),
    "f1000": Source(tuple("https://f1000research.com/gateways/elixir" + query for query in (
        "", "?selectedDomain=documents", "?selectedDomain=posters", "?selectedDomain=slides",
    )) + (
        "https://f1000research.com/documents/13-80",
        "https://f1000research.com/documents/15-1717",
        "https://f1000research.com/articles/11-1265/v2",
    ), discover=f1000, sections=(4, 8, 9), paths=("/gateways/elixir",), query_keys=("selectedDomain", "show", "page")),
    "zenodo": Source((
        "https://zenodo.org/api/records?q=communities:elixir&size=25&sort=mostrecent",
        "https://zenodo.org/api/records/17202558",
    ), discover=zenodo, sections=(5, 8)),
    "zenodo-project-plans": Source(("https://zenodo.org/api/records?" + urlencode({
        "q": '(elixir OR communities:elixir) AND title:("work plan" OR "project plan" OR "work programme" '
             'OR "work program" OR workplan OR "action plan" OR "implementation plan" OR "project proposal" '
             'OR "grant proposal" OR roadmap OR "community proposal")',
        "all_versions": "true", "size": 25, "sort": "mostrecent",
    }),), discover=zenodo, sections=(24,), formats=PROJECT_DOCUMENTS),
    "systems-biology": Source((
        "https://arxiv.org/abs/2609.13127", "https://arxiv.org/pdf/2609.13127",
    ), discover=files, sections=(9,)),
    **{
        f"cordis-{project}": Source(tuple(
            f"https://cordis.europa.eu/project/id/{grant}{page}" for page in ("", "/results", "/reporting")
        ), sections=(17,), paths=(), formats=PROJECT_DOCUMENTS)
        for project, grant in EU_PROJECTS.items()
    },
    **{
        f"zenodo-{project}": Source(("https://zenodo.org/api/records?" + urlencode({
            "q": f"(communities:elixir-steers OR grants.code:{grant})" if project == "steers" else f"grants.code:{grant}",
            "all_versions": "true", "size": 25, "sort": "mostrecent",
        }),), discover=zenodo, sections=(18,), formats=PROJECT_DOCUMENTS)
        for project, grant in EU_PROJECTS.items()
    },
    "project-pages": Source(tuple("https://elixir-europe.org" + path for path in (
        "/how-we-work/scientific-programme/technology/24-compute",
        "/how-we-work/scientific-programme/science/hdtr/fair-fega",
    )), sections=(18,), paths=(), browser=True),
    "node-czech": Source((
        "https://www.elixir-czech.cz/about-elixir-cz",
        "https://www.elixir-czech.cz/communities",
        "https://www.elixir-czech.cz/elixir-cz-strategy/elixir-cz-strategy-2026-2030",
    ), sections=(19,), paths=("/about-elixir-cz", "/communities", "/elixir-cz-strategy")),
    "node-finland": Source((
        "https://www.elixir-finland.org/en/elixir-2/",
        "https://www.elixir-finland.org/en/publications-and-reports/",
        "https://csc.fi/contact/juha-tornroos/",
    ), sections=(19,), paths=()),
    "node-luxembourg": Source((
        "https://elixir-luxembourg.org/about-node/", "https://elixir-luxembourg.org/projects/",
    ), sections=(19,), paths=("/about-node/", "/projects/")),
    "node-netherlands": Source((
        "https://www.health-ri.nl/elixir/organisatie",
        "https://www.health-ri.nl/en/elixir/contact",
        "https://www.health-ri.nl/en/projects-collaborations/elixir-node-support",
        "https://www.health-ri.nl/en/about/organisation/international",
    ), sections=(19,), paths=("/elixir/", "/en/elixir/")),
    "node-france": Source((
        "https://www.ifb-elixir.fr/en/ifb-elixir-fr/ifb-core-the-coordinating-unit/",
        "https://www.ifb-elixir.fr/en/rd-innovation/project/elixir-steers/",
    ), sections=(19,), paths=("/en/ifb-elixir-fr/", "/en/rd-innovation/")),
    "node-norway": Source((
        "https://elixir.no/about/", "https://elixir.no/funding-and-projects/",
    ), sections=(19,), paths=("/about/", "/funding-and-projects/")),
    "node-portugal": Source((
        "https://biodata.pt/about", "https://biodata.pt/elixir-pt",
        "https://fegaportugal.biodata.pt/about/about-us",
        "https://biodata.pt/news/biodatapt-leads-work-packages-new-elixir-projects",
    ), sections=(19,), paths=("/about", "/elixir-pt"), exclude_paths=("/news/",)),
    "node-switzerland": Source((
        "https://www.sib.swiss/groups", "https://www.sib.swiss/directory?query=Alexander+Kanitz",
        "https://www.sib.swiss/activities/efficient-coordination-across-institutions-disciplines-and-borders",
    ), sections=(19,), paths=("/groups",), listing_paths=("/directory",), browser=True,
       render_waits={"/groups": ".search-result-container > *", "/directory": ".search-result-container > *"}),
    "europepmc-systems-biology": Source((
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
            "query": 'TITLE_ABS:"systems biology" AND PUB_TYPE:review AND FIRST_PDATE:[2022-01-01 TO 2026-11-10]',
            "format": "json", "resultType": "core", "pageSize": 100,
        }),
    ), discover=europepmc, sections=(20,)),
    "fairsharing": Source(("https://fairsharing.org/",), sections=(12,),
                          deferred="Requires a FAIRsharing account; access not supplied."),
    "community-minutes": Source((
        "https://docs.google.com/document/d/1BdJVO_5W3bywl8L5mLu66jRbZmjiWIPTsRjD6kNuejo/edit",
    ), sections=(13,), deferred="Carissa must confirm permission.", access="restricted"),
    "community-f2f": Source((
        "https://docs.google.com/document/d/1dMFnvVqOC9leNQ-switvz_d_9CZoglM7ePXhKHBZBBE/edit",
        "https://docs.google.com/presentation/d/1o9G6B3LoJrht1mIGAf6mzbdIgyI0LAEarpjkR5LQzWE/edit",
    ), sections=(14,), deferred="Internal agenda and slides require permission.", access="restricted"),
    "node-structure": Source((), sections=(15,), deferred="Awaiting file and permission from Xenia.", access="restricted"),
    "commissioned-plans": Source((), sections=(16,), deferred="Awaiting files, permission and budget redaction from Xenia.", access="restricted"),
    "project-participation": Source((), sections=(21,), access="restricted",
                                   deferred="Awaiting approved task assignments, funded/in-kind status and effort records for the example projects."),
    "group-activity": Source((), sections=(22,), access="restricted",
                             deferred="Awaiting approved group rosters, work plans and participation summaries; link access alone is not permission."),
    "bid-outcomes": Source((), sections=(23,), access="restricted",
                           deferred="Awaiting approved redacted bid records and outcomes, including unsuccessful applications."),
}
