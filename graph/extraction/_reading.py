import json
import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Protocol, cast

import pymupdf
from bs4 import BeautifulSoup, Tag

from ..paths import PROJECT_ROOT

INDEX = PROJECT_ROOT / "data" / "input" / "data-sources-scraping.jsonl"
DROPPED_TAGS = ("script", "style", "noscript", "svg", "nav", "header", "footer", "form", "iframe", "button")
PERSON_LINK = re.compile(r"^/users/|^/people/[^/]+/?$|embl\.org/people/person/")
DROPPED_CLASSES = re.compile(
    r"(^|[-_ ])(menu|breadcrumb|visually-hidden|cookie|navbar|skip-link|social|share|pager)([-_ ]|$)"
)


@cache
def source_urls() -> dict[str, str]:
    urls: dict[str, str] = {}
    with INDEX.open(encoding="utf-8") as stream:
        for line in stream:
            row = cast(dict[str, object], json.loads(line))
            path, url = row.get("path"), row.get("final_url") or row.get("url")
            if row.get("status") == "saved" and isinstance(path, str) and isinstance(url, str):
                urls[path] = url
    return urls


def url_of(path: Path) -> str | None:
    return source_urls().get(path.relative_to(PROJECT_ROOT).as_posix())


def _link(tag: Tag) -> str:
    label = " ".join(tag.get_text(" ", strip=True).split())
    href = str(tag.get("href") or "")
    if not href.startswith(("http", "mailto:", "/")) or href in label:
        return label
    return f"{label} <{href}>" if label else f"<{href}>"


def _clean(root: Tag | BeautifulSoup) -> None:
    for tag in root.find_all(DROPPED_TAGS):
        tag.decompose()
    for tag in root.find_all(class_=DROPPED_CLASSES):
        if tag.parent is not None:
            tag.decompose()
    for anchor in root.find_all("a"):
        anchor.replace_with(_link(anchor))


def rendered(tag: Tag) -> str:
    copy = BeautifulSoup(str(tag), "lxml")
    _clean(copy)
    return " ".join(copy.get_text(" ").split())


def html_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    title = " ".join(soup.title.get_text(" ", strip=True).split()) if soup.title else ""
    root = soup.find("main") or soup.body or soup
    _clean(root)
    lines = [" ".join(line.split()) for line in root.get_text("\n").splitlines()]
    body = "\n".join(line for line in lines if line)
    return f"Page title: {title}\n\n{body}" if title else body


class PdfPage(Protocol):
    def get_text(self) -> str: ...


class Pdf(Protocol):
    page_count: int

    def load_page(self, page_id: int) -> PdfPage: ...


def pdf_text(path: Path) -> str:
    with pymupdf.open(path) as document:
        pdf = cast(Pdf, document)
        pages = [f"[page {number + 1}]\n{pdf.load_page(number).get_text()}" for number in range(pdf.page_count)]
    return "\n".join(re.sub(r"[ \t]+", " ", page) for page in pages)


def person_links(path: Path) -> list[str]:
    if path.suffix.lower() != ".html":
        return []
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    root = soup.find("main") or soup.body or soup
    names = (" ".join(anchor.get_text(" ", strip=True).split()) for anchor in root.find_all("a", href=PERSON_LINK))
    return list(dict.fromkeys(name for name in names if 2 <= len(name.split()) <= 6 and not name.endswith(("…", "..."))))


def document_text(path: Path) -> str:
    return pdf_text(path) if path.suffix.lower() == ".pdf" else html_text(path)


def squashed(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-z]+", "", folded.lower())
