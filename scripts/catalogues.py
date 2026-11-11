import json
import re
import sys
from collections.abc import Iterator
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "input"
OUTPUT = ROOT / "data" / "extracted" / "catalogues"


def text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    plain = BeautifulSoup(value, "lxml").get_text(" ") if "<" in value else unescape(value)
    return re.sub(r"\s+", " ", plain).strip() or None


def strings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [cleaned for value in values if (cleaned := text(value))]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def biotools() -> Iterator[dict]:
    seen: set[str] = set()
    for path in sorted((INPUT / "biotools").glob("*.json")):
        for tool in load(path)["list"]:
            if tool["biotoolsID"] in seen:
                continue
            seen.add(tool["biotoolsID"])
            credits = [credit for credit in tool.get("credit") or [] if credit.get("name")]
            yield {
                "biotools_id": tool["biotoolsID"],
                "name": text(tool.get("name")),
                "description": text(tool.get("description")),
                "homepage": tool.get("homepage"),
                "tool_types": strings(tool.get("toolType")),
                "topic_uris": [topic["uri"] for topic in tool.get("topic") or [] if topic.get("uri")],
                "topic_labels": [topic["term"] for topic in tool.get("topic") or [] if topic.get("term")],
                "elixir_nodes": strings(tool.get("elixirNode")),
                "elixir_platforms": strings(tool.get("elixirPlatform")),
                "elixir_communities": strings(tool.get("elixirCommunity")),
                "collections": strings(tool.get("collectionID")),
                "credit_names": [text(credit["name"]) or "" for credit in credits],
                "credit_orcids": [credit.get("orcidid") or "" for credit in credits],
                "credit_emails": [credit.get("email") or "" for credit in credits],
                "credit_types": [credit.get("typeEntity") or "" for credit in credits],
                "publication_dois": [p["doi"] for p in tool.get("publication") or [] if p.get("doi")],
                "addition_date": tool.get("additionDate"),
                "last_update": tool.get("lastUpdate"),
                "source_path": relative(path),
            }


def tess(folder: str) -> Iterator[dict]:
    seen: set[str] = set()
    for path in sorted((INPUT / folder).glob("*.json")):
        for item in load(path)["data"]:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            attributes = item["attributes"]
            relations = item["relationships"]
            topics = attributes.get("scientific-topics") or []
            record = {
                "tess_id": item["id"],
                "title": text(attributes.get("title")),
                "url": attributes.get("url"),
                "description": text(attributes.get("description")),
                "keywords": strings(attributes.get("keywords")),
                "topic_uris": [topic["uri"] for topic in topics if topic.get("uri")],
                "topic_labels": [topic["preferred-label"] for topic in topics if topic.get("preferred-label")],
                "node_ids": [node["id"] for node in relations["nodes"]["data"]],
                "collection_ids": [collection["id"] for collection in relations["collections"]["data"]],
                "content_provider_id": (relations["content-provider"]["data"] or {}).get("id"),
                "source_path": relative(path),
            }
            if folder == "tess-events":
                record |= {
                    "start": attributes.get("start"),
                    "end": attributes.get("end"),
                    "online": attributes.get("online"),
                    "city": text(attributes.get("city")),
                    "country": text(attributes.get("country")),
                    "organizer": text(attributes.get("organizer")),
                    "host_institutions": strings(attributes.get("host-institutions")),
                    "event_types": strings(attributes.get("event-types")),
                }
            else:
                record |= {
                    "doi": attributes.get("doi"),
                    "authors": strings(attributes.get("authors")),
                    "resource_types": strings(attributes.get("resource-type")),
                    "date_published": attributes.get("date-published") or attributes.get("date-created"),
                }
            yield record


def tess_facets() -> Iterator[dict]:
    for folder in ("tess-events", "tess-materials"):
        path = sorted((INPUT / folder).glob("*.json"))[0]
        facets = load(path)["meta"]["available-facets"]
        for facet in ("node", "collections", "content-provider"):
            for entry in facets.get(facet, []):
                yield {
                    "catalogue": folder.removeprefix("tess-"),
                    "facet": facet,
                    "value": text(entry["value"]),
                    "count": entry["count"],
                    "source_path": relative(path),
                }


def zenodo() -> Iterator[dict]:
    records: dict[int, tuple[Path, dict, list[str]]] = {}
    for path in sorted(INPUT.glob("*/*.json")):
        if "api-records-" not in path.name:
            continue
        record = load(path)
        if "metadata" not in record or "id" not in record:
            continue
        if record["id"] in records:
            records[record["id"]][2].append(relative(path))
        else:
            records[record["id"]] = (path, record, [relative(path)])
    for record_id in sorted(records):
        path, record, paths = records[record_id]
        metadata = record["metadata"]
        creators = metadata.get("creators") or []
        grants = metadata.get("grants") or []
        yield {
            "record_id": str(record_id),
            "concept_record_id": str(record.get("conceptrecid") or ""),
            "doi": record.get("doi") or metadata.get("doi"),
            "concept_doi": record.get("conceptdoi"),
            "url": (record.get("links") or {}).get("self_html") or (record.get("links") or {}).get("html"),
            "title": text(metadata.get("title")),
            "publication_date": metadata.get("publication_date"),
            "version": text(metadata.get("version")),
            "resource_type": (metadata.get("resource_type") or {}).get("title")
            or (metadata.get("resource_type") or {}).get("type"),
            "description": text(metadata.get("description")),
            "keywords": strings(metadata.get("keywords")),
            "communities": [c["id"] for c in metadata.get("communities") or [] if c.get("id")],
            "grant_codes": [g.get("code") or "" for g in grants],
            "grant_acronyms": [g.get("acronym") or "" for g in grants],
            "creator_names": [text(c.get("name")) or "" for c in creators],
            "creator_orcids": [c.get("orcid") or "" for c in creators],
            "creator_affiliations": [text(c.get("affiliation")) or "" for c in creators],
            "file_names": [f.get("key") or "" for f in record.get("files") or []],
            "source_path": relative(path),
            "source_paths": paths,
        }


def europepmc() -> Iterator[dict]:
    seen: set[str] = set()
    for path in sorted((INPUT / "europepmc-systems-biology").glob("*.json")):
        for paper in load(path)["resultList"]["result"]:
            if paper["id"] in seen:
                continue
            seen.add(paper["id"])
            authors = (paper.get("authorList") or {}).get("author") or []
            yield {
                "epmc_id": f"{paper.get('source')}:{paper['id']}",
                "pmid": paper.get("pmid"),
                "doi": paper.get("doi"),
                "title": text(paper.get("title")),
                "journal": text(((paper.get("journalInfo") or {}).get("journal") or {}).get("title")),
                "pub_year": paper.get("pubYear"),
                "first_publication_date": paper.get("firstPublicationDate"),
                "author_names": [text(a.get("fullName")) or "" for a in authors],
                "author_orcids": [
                    ((a.get("authorId") or {}).get("value") if (a.get("authorId") or {}).get("type") == "ORCID" else "")
                    or ""
                    for a in authors
                ],
                "keywords": strings((paper.get("keywordList") or {}).get("keyword")),
                "mesh_terms": [
                    m["descriptorName"]
                    for m in (paper.get("meshHeadingList") or {}).get("meshHeading") or []
                    if m.get("descriptorName")
                ],
                "abstract": text(paper.get("abstractText")),
                "cited_by_count": paper.get("citedByCount"),
                "source_path": relative(path),
            }


def keywords(soup: BeautifulSoup) -> list[str]:
    for title in soup.select("div.asset-subcontainer__title"):
        if title.get_text(strip=True).lower() == "keywords" and title.parent:
            text_after = title.parent.get_text(" ", strip=True).removeprefix(title.get_text(" ", strip=True))
            return [part.strip() for part in text_after.split(",") if part.strip()]
    return []


def iso_date(value: str | None) -> str | None:
    return value.replace("/", "-") if value else None


def f1000() -> Iterator[dict]:
    for path in sorted((INPUT / "f1000").glob("*.html")):
        kind = path.name.split("-")[0]
        if kind not in {"articles", "documents", "posters", "slides"} or "-pdf-" in path.name:
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
        meta: dict[str, list[str]] = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property")
            if name and tag.get("content"):
                meta.setdefault(str(name).lower(), []).append(str(tag["content"]))
        title = (meta.get("dc.title") or meta.get("citation_title") or [None])[0]
        if not title:
            continue
        doi = next((v for v in meta.get("dc.identifier", []) + meta.get("citation_doi", []) if "10." in v), None)
        yield {
            "item_path": relative(path),
            "kind": kind.removesuffix("s"),
            "title": text(title),
            "description": text((meta.get("dc.description") or [None])[0]),
            "subjects": [k for k in dict.fromkeys([*(s.strip() for v in meta.get("dc.subject", []) for s in v.split(",")), *keywords(soup)]) if k],
            "creator_names": [text(v) or "" for v in meta.get("dc.creator") or meta.get("citation_author", [])],
            "date": iso_date((meta.get("dc.date") or meta.get("citation_publication_date") or meta.get("citation_date") or [None])[0]),
            "doi": re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi) if doi else None,
            "source_path": relative(path),
        }


CATALOGUES = {
    "biotools": biotools,
    "tess_events": lambda: tess("tess-events"),
    "tess_materials": lambda: tess("tess-materials"),
    "tess_facets": tess_facets,
    "zenodo_records": zenodo,
    "europepmc_reviews": europepmc,
    "f1000_items": f1000,
}


def main(names: list[str]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name in names or list(CATALOGUES):
        target = OUTPUT / f"{name}.jsonl"
        count = 0
        with target.open("w", encoding="utf-8") as stream:
            for row in CATALOGUES[name]():
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
        print(f"{relative(target)}: {count}")


if __name__ == "__main__":
    main(sys.argv[1:])
