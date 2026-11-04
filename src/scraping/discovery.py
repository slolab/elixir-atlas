from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

DOCUMENTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".odt", ".odp", ".ods", ".txt", ".csv", ".tsv", ".xls", ".xlsx", ".json", ".xml"}
MEDIA = {".mp4", ".webm", ".mov", ".mp3", ".wav", ".m4v"}
ASSETS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".css", ".js", ".woff", ".woff2", ".zip", ".gz", ".tar", ".ics"}
PRIVATE = re.compile(r"/(?:intranet|admin|administrator|login|logout|register|user/(?:login|password|register)|elixir-sso|wp-admin|wp-login\.php|search)(?:/|$)", re.I)


def normalize(url):
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username:
        return None
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.startswith("utm_") and k not in ("fbclid", "gclid")]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", urlencode(sorted(query)), ""))


def host(url):
    return urlsplit(url).netloc.lower().removeprefix("www.")


def extension(url):
    return Path(unquote(urlsplit(url).path)).suffix.lower()


def is_document(url):
    return extension(url) in DOCUMENTS or urlsplit(url).path.endswith("/pdf") or (
        host(url) == "arxiv.org" and urlsplit(url).path.startswith("/pdf/")) or (
        host(url) == "drive.google.com" and urlsplit(url).path == "/uc")


def pagination_url(current, following, kind):
    p = urlsplit(urljoin(current, following))
    query = dict(parse_qsl(urlsplit(current).query))
    query.update(parse_qsl(p.query))
    path = p.path
    if kind == "tess" and not path.endswith(".json_api"):
        path += ".json_api"
    return normalize(urlunsplit((p.scheme, p.netloc, path, urlencode(query), "")))


def excluded(url, source):
    if host(url) not in {host(seed) for seed in source.urls} or url in source.urls:
        return False
    p = urlsplit(url)
    if p.path.rstrip("/") in source.listing_paths:
        return bool(p.query)
    return any(p.path.startswith(prefix) for prefix in source.exclude_paths)


def page_allowed(url, source):
    p = urlsplit(url)
    return (host(url) in {host(seed) for seed in source.urls}
            and any(p.path.startswith(prefix) for prefix in source.paths)
            and not PRIVATE.search(p.path)
            and not excluded(url, source)
            and extension(url) not in ASSETS | MEDIA
            and all(k in source.query_keys for k, _ in parse_qsl(p.query)))


@dataclass
class Discovery:
    links: list[tuple[str, str]] = field(default_factory=list)
    group: str = ""
    ids: list[str] = field(default_factory=list)
    total: int | None = None


def files(body, current, content_type, source):
    return Discovery()


def website(body, current, content_type, source):
    if host(current) == "zenodo.org" and urlsplit(current).path.startswith("/api/records"):
        return zenodo(body, current, content_type, source)
    if "html" not in content_type or urlsplit(current).path.rstrip("/") in source.listing_paths:
        return Discovery()
    drive = re.fullmatch(r"/file/d/([\w-]+)/(?:view|preview)", urlsplit(current).path)
    if host(current) == "drive.google.com" and drive:
        return Discovery([(f"https://drive.google.com/uc?export=download&id={drive[1]}", "download")])
    soup = BeautifulSoup(body, "html.parser")
    links = [a.get("href") for a in soup.select("a[href]")]
    links += [m.get("content") for m in soup.select('meta[name="citation_pdf_url"]')]
    links += [f.get("src") for f in soup.select('iframe[src*="youtube"], iframe[src*="vimeo"]')]
    result = Discovery()
    for link in links:
        try:
            url = normalize(urljoin(current, link or ""))
        except ValueError:
            continue
        if not url or excluded(url, source):
            continue
        drive = re.fullmatch(r"/file/d/([\w-]+)/(?:view|preview)", urlsplit(url).path)
        if host(url) == "drive.google.com" and drive:
            result.links.append((f"https://drive.google.com/uc?export=download&id={drive[1]}", "download"))
        elif extension(url) in MEDIA or host(url) in ("youtube.com", "youtu.be", "vimeo.com"):
            result.links.append((url, "video"))
        elif extension(url) in source.formats or (is_document(url) and extension(url) not in DOCUMENTS and ".pdf" in source.formats):
            result.links.append((url, "download"))
        elif is_document(url):
            continue
        elif host(url) == "zenodo.org" and re.fullmatch(r"/records?/\d+/?", urlsplit(url).path):
            result.links.append(("https://zenodo.org/api/records/" + urlsplit(url).path.strip("/").split("/")[-1], "download"))
        elif page_allowed(url, source):
            result.links.append((url, "download"))
    return result


def catalogue(body, current, content_type, source, kind):
    if "json" not in content_type:
        raise ValueError("Expected a JSON catalogue")
    data = json.loads(body)
    records = data["list" if kind == "biotools" else "data"]
    if not isinstance(records, list):
        raise ValueError("Expected a list of catalogue records")
    result = Discovery(group=kind, ids=[str(r["biotoolsID" if kind == "biotools" else "id"]) for r in records],
                       total=int(data["count"] if kind == "biotools" else data["meta"]["results-count"]))
    following = data.get("next") if kind == "biotools" else data["links"].get("next")
    if following:
        result.links.append((pagination_url(current, following, kind), "download"))
    if result.total and not records:
        raise ValueError("Non-empty catalogue returned an empty page")
    return result


def biotools(body, current, content_type, source):
    return catalogue(body, current, content_type, source, "biotools")


def tess(body, current, content_type, source):
    return catalogue(body, current, content_type, source, "tess")


def zenodo(body, current, content_type, source):
    if not re.fullmatch(r"/api/records(?:/\d+)?", urlsplit(current).path):
        return Discovery()
    if "json" not in content_type:
        raise ValueError("Expected Zenodo record JSON")
    data = json.loads(body)
    if "hits" in data:
        ids = [str(record["id"]) for record in data["hits"]["hits"]]
        total = data["hits"]["total"]
        result = Discovery(group="records", ids=ids, total=total["value"] if isinstance(total, dict) else total)
        result.links = [(f"https://zenodo.org/api/records/{id_}", "download") for id_ in ids]
        if following := data.get("links", {}).get("next"):
            result.links.append((following, "download"))
        return result
    result = Discovery()
    for file in data.get("files", []):
        suffix = Path(file["key"]).suffix.lower()
        action = "download" if suffix in source.formats | {".html", ".htm"} else "video" if suffix in MEDIA else "unsupported"
        result.links.append((file["links"]["self"], action))
    return result


def f1000(body, current, content_type, source):
    if "html" not in content_type:
        return Discovery()
    if host(current) != "f1000research.com":
        return website(body, current, content_type, source)
    soup = BeautifulSoup(body, "html.parser")
    if urlsplit(current).path.rstrip("/") == "/gateways/elixir":
        group = dict(parse_qsl(urlsplit(current).query)).get("selectedDomain", "articles").lower()
        total = soup.select_one(".js-pagination-results-total")
        if total is None:
            raise ValueError("F1000 listing has no result count")
        urls = [a["href"] for a in soup.select("a.article-link[href]")] if group == "articles" else re.findall(
            r'''href=["'](/(?:documents|posters|slides)/[\w-]+(?:/v\d+)?)["']''', body.decode(errors="replace"))
        urls = sorted({normalize(urljoin(current, url)) for url in urls})
        result = Discovery(group=group, ids=[urlsplit(url).path.split("/")[2] for url in urls],
                           total=int(total.get_text(strip=True).replace(",", "")))
        result.links = [(url, "download") for url in urls]
        result.links += [(urljoin(current, a["href"]), "download") for a in soup.select("a.js-pagination-next[href]")]
        if result.total and not result.ids:
            raise ValueError(f"F1000 {group} listing advertises records but none were discovered")
        return result

    links = [m["content"] for m in soup.select('meta[name="citation_pdf_url"][content]')]
    links += [a["data-url"] for a in soup.select("a.js-download[data-url]")]
    result = Discovery([(urljoin(current, url), "download") for url in links])
    if re.fullmatch(r"/(articles|documents|posters|slides)/[\w-]+(?:/v\d+)?", urlsplit(current).path) and not links:
        raise ValueError("F1000 publication has no PDF download link")
    return result
