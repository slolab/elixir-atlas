from dataclasses import dataclass
from typing import Callable

from discovery import DOCUMENTS, biotools, tess, website, f1000, zenodo, files


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


SOURCES = {
    "biotools": Source(("https://bio.tools/api/t/?format=json&per_page=100&sort=additionDate&ord=asc",), discover=biotools, sections=(10,)),
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
    "systems-biology": Source((
        "https://arxiv.org/abs/2609.13127", "https://arxiv.org/pdf/2609.13127",
    ), discover=files, sections=(9,)),
    "fairsharing": Source(("https://fairsharing.org/",), sections=(12,),
                          deferred="Requires a FAIRsharing account; access not supplied."),
    "community-minutes": Source((
        "https://docs.google.com/document/d/1BdJVO_5W3bywl8L5mLu66jRbZmjiWIPTsRjD6kNuejo/edit",
    ), sections=(13,), deferred="Carissa must confirm permission."),
    "community-f2f": Source((
        "https://docs.google.com/document/d/1dMFnvVqOC9leNQ-switvz_d_9CZoglM7ePXhKHBZBBE/edit",
        "https://docs.google.com/presentation/d/1o9G6B3LoJrht1mIGAf6mzbdIgyI0LAEarpjkR5LQzWE/edit",
    ), sections=(14,), deferred="Internal agenda and slides require permission."),
    "node-structure": Source((), sections=(15,), deferred="Awaiting file and permission from Xenia."),
    "commissioned-plans": Source((), sections=(16,), deferred="Awaiting files, permission and budget redaction from Xenia."),
}
