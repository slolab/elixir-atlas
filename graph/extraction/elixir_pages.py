import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Literal
from urllib.parse import urljoin

from biotope.extraction import Document, ExtractionError, Extractor, Schema
from bs4 import BeautifulSoup, Tag

from ._reading import url_of

SITE = "https://elixir-europe.org"
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
PERIOD = re.compile(r"\((\d{4})\s*[–-]\s*(\d{2,4})\)")
DAY = re.compile(rf"(\d{{1,2}})\s+({MONTHS}|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*,?\s+(\d{{4}})", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def located(value: object, locator: str) -> dict[str, Any]:
    return {"value": value, "locator": locator}


def quoted(value: object, quote: str) -> dict[str, Any]:
    return {"value": value, "quote": quote}


def page(document: Document) -> tuple[BeautifulSoup, Tag]:
    soup = BeautifulSoup(document.path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    main = soup.find("main")
    if not isinstance(main, Tag):
        raise ExtractionError(f"{document.path.name}: no main content")
    return soup, main


def words(tag: Tag) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())


def month(name: str, year: str) -> str:
    return datetime.strptime(f"{name[:3]} {year}", "%b %Y").strftime("%Y-%m")


def day(text: str) -> str | None:
    match = DAY.search(text)
    if not match:
        return None
    return datetime.strptime(f"{match.group(1)} {match.group(2)[:3]} {match.group(3)}", "%d %b %Y").date().isoformat()


@dataclass(frozen=True, kw_only=True)
class GroupDirectoryEntry:
    """One entry of the ELIXIR website's directory of its Communities, Platforms and Focus Groups: the
    /communities, /platforms and /focus-groups listing pages, and the archive note on a former Community's page.
    The directory defines which groups are ELIXIR Communities, Platforms and Focus Groups and whether each is
    current or past."""

    __record_key__: ClassVar[tuple[str, ...]] = ("name",)

    name: str = field(metadata={"description": "The group's name as the directory writes it."})
    kind: Literal["community", "platform", "focus_group"] = field(
        metadata={"description": "The directory section the entry is listed in."}
    )
    status: Literal["current", "past"] = field(
        metadata={"description": "current when the directory lists the group as current; past for past or archived groups."}
    )
    url: str = field(metadata={"description": "The group's page on the ELIXIR website, as the directory links it."})
    start: str | None = field(metadata={"description": "Start year of a past group's period, as YYYY."})
    end: str | None = field(metadata={"description": "End year of a past group's period, as YYYY."})
    became: str | None = field(
        metadata={"description": "The group or project this group became or moved its activities to, as written."}
    )
    became_date: str | None = field(metadata={"description": "When it became that group, as YYYY-MM."})


class GroupDirectoryReader(Extractor):
    name = "group-directory-reader"
    version = "1"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        _, main = page(document)
        name = document.path.name
        if name.startswith("communities-marine-metagenomics-"):
            return self.archived(main)
        if name.startswith("focus-groups-"):
            return self.focus_groups(main)
        kind = "platform" if name.startswith("platforms-") else "community"
        records: list[dict[str, Any]] = []
        for card in main.select("div.tinted.rounded"):
            link = card.select_one("h3 a")
            if not isinstance(link, Tag):
                continue
            label = words(link)
            where = f"{kind} card: {label}"
            records.append(self.entry(label, kind, "current", urljoin(SITE, str(link["href"]).strip()), where))
        if not records:
            raise ExtractionError(f"{name}: no directory cards")
        return records

    def entry(self, label: str, kind: str, status: str, url: str, where: str, **values: dict[str, Any]) -> dict[str, Any]:
        blank = located(None, where)
        return {
            "name": located(label, where),
            "kind": located(kind, where),
            "status": located(status, where),
            "url": located(url, where),
            "start": values.get("start", blank),
            "end": values.get("end", blank),
            "became": values.get("became", blank),
            "became_date": values.get("became_date", blank),
        }

    def focus_groups(self, main: Tag) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for heading in main.find_all("h2"):
            title = words(heading)
            status = {"Current Focus Groups": "current", "Past Focus Groups": "past"}.get(title)
            listing = heading.find_next_sibling("ul")
            if status is None or not isinstance(listing, Tag):
                continue
            for item in listing.find_all("li", recursive=False):
                link = item.find("a")
                if not isinstance(link, Tag):
                    continue
                text = words(item)
                values: dict[str, dict[str, Any]] = {}
                if period := PERIOD.search(text):
                    end = period.group(2)
                    values["start"] = quoted(period.group(1), text)
                    values["end"] = quoted(end if len(end) == 4 else period.group(1)[:2] + end, text)
                if became := re.search(rf"({MONTHS})\s+(\d{{4}}),?\s+this group(?:'s| ’s|’s)?\s*(?:activities|work)?\s*(?:became|transitioned to|moved to)\s+the\s+(.+?)\s*$", text, re.I):
                    values["became"] = quoted(became.group(3), text)
                    values["became_date"] = quoted(month(became.group(1), became.group(2)), text)
                url = urljoin(SITE, str(link["href"]).strip())
                records.append(self.entry(words(link), "focus_group", status, url, f"{title}: {words(link)}", **values))
        if not records:
            raise ExtractionError("focus group directory without lists")
        return records

    def archived(self, main: Tag) -> list[dict[str, Any]]:
        text = words(main)
        match = re.search(rf"In ({MONTHS}) (\d{{4}}) the (.+?) became the (.+?)\s*\.", text)
        if not match:
            raise ExtractionError("archived Community page without its transition")
        quote = match.group(0)
        return [
            self.entry(
                match.group(3),
                "community",
                "past",
                f"{SITE}/communities/marine-metagenomics",
                "archive note",
                became=quoted(match.group(4), quote),
                became_date=quoted(month(match.group(1), match.group(2)), quote),
            )
        ]


@dataclass(frozen=True, kw_only=True)
class ElixirPage:
    """Facts that an ELIXIR website page states in its structure: its publication and last-modified dates, the
    contact email links it gives, and its join button with the text beside it. One record per page."""

    published: str | None = field(metadata={"description": "The page's datePublished, as YYYY-MM-DD."})
    modified: str | None = field(metadata={"description": "The page's dateModified, as YYYY-MM-DD."})
    contacts: list[str] = field(
        metadata={"description": "Each contact email address as the page shows it to the reader, in page order."}
    )
    contact_targets: list[str] = field(
        metadata={"description": "The address each contact link actually sends to (its mailto target), in the same order as contacts."}
    )
    join_url: str | None = field(metadata={"description": "Where the page's 'Join this Community' or 'Join this group' button leads."})
    joining: str | None = field(
        metadata={"description": "The text the page gives beside its join button: how to join, approval, onboarding and contact."}
    )


class ElixirPageReader(Extractor):
    name = "elixir-page-reader"
    version = "2"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        soup, main = page(document)
        raw = str(soup)
        dates = {key: re.search(rf'"{key}":"(\d{{4}}-\d{{2}}-\d{{2}})', raw) for key in ("datePublished", "dateModified")}
        contacts: list[dict[str, Any]] = []
        targets: list[dict[str, Any]] = []
        for link in main.find_all("a", href=re.compile(r"^\s*mailto:", re.I)):
            target = str(link["href"]).strip()[7:].split("?")[0].strip().lower()
            shown = words(link)
            written = EMAIL.search(shown)
            visible = (written.group(0) if written else target).lower()
            contacts.append(quoted(visible, shown or target))
            targets.append(quoted(target, str(link["href"]).strip()))
        button = main.find("a", string=re.compile(r"^\s*Join this", re.I))
        join_url = urljoin(SITE, str(button["href"]).strip()) if isinstance(button, Tag) else None
        block = button.find_parent(class_="paragraph--type--find-out-more") if isinstance(button, Tag) else None
        joining = None
        if isinstance(block, Tag):
            for link in block.find_all("a", href=True):
                href = urljoin(SITE, str(link["href"]).strip())
                if link is not button and not href.startswith("mailto:"):
                    link.replace_with(f"{words(link)} ({href})")
            text = words(block)
            joining = re.sub(r"\s*Join this (Community|group)\s*$", "", text, flags=re.I) or None
        return [
            {
                "published": located(dates["datePublished"].group(1) if dates["datePublished"] else None, "JSON-LD datePublished"),
                "modified": located(dates["dateModified"].group(1) if dates["dateModified"] else None, "JSON-LD dateModified"),
                "contacts": contacts,
                "contact_targets": targets,
                "join_url": located(join_url, "join button"),
                "joining": quoted(joining, joining) if joining else located(None, "join button"),
            }
        ]


@dataclass(frozen=True, kw_only=True)
class ElectionCandidate:
    """A candidate in the ELIXIR Community co-lead election, as the election page's candidate table lists them.
    Candidacy is not a role: a candidate is neither a co-lead nor, from this page alone, a Community member."""

    __record_key__: ClassVar[tuple[str, ...]] = ("community", "person")

    community: str = field(metadata={"description": "The Community the candidate stands for, as written."})
    person: str = field(metadata={"description": "The candidate's name."})
    country: str | None = field(metadata={"description": "The country or EMBL site given with the candidate."})
    affiliation: str | None = field(metadata={"description": "The candidate's organisation, as written."})
    note: str | None = field(metadata={"description": "A note beside the name, such as 'application withdrawn' or 'reapplying'."})
    year: int = field(metadata={"description": "The election year the table is for."})


class ElectionReader(Extractor):
    name = "election-reader"
    version = "1"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        _, main = page(document)
        table = next((t for t in main.find_all("table") if "Candidate and affiliation" in words(t)), None)
        caption = re.search(r"(\d{4}) Community co-lead candidates", words(main))
        if not isinstance(table, Tag) or not caption:
            raise ExtractionError(f"{document.path.name}: no candidate table")
        year = int(caption.group(1))
        records: list[dict[str, Any]] = []
        community = ""
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) == 4:
                community = words(cells[0])
                cells = cells[1:]
            if len(cells) != 3:
                raise ExtractionError(f"{document.path.name}: unexpected candidate row")
            lines = [line for line in cells[0].stripped_strings]
            quote = " ".join(lines)
            note = next((line.strip("()") for line in lines[1:] if line.startswith("(")), None)
            origin = next((line for line in lines[1:] if "·" in line), None)
            country, _, affiliation = (origin or "").partition("·")
            records.append(
                {
                    "community": quoted(community, community),
                    "person": quoted(lines[0], quote),
                    "country": quoted(country.strip() or None, quote),
                    "affiliation": quoted(affiliation.strip() or None, quote),
                    "note": quoted(note, quote),
                    "year": located(year, f"{year} Community co-lead candidates"),
                }
            )
        return records


@dataclass(frozen=True, kw_only=True)
class ElixirEvent:
    """An event the ELIXIR website lists: its events listing and its event pages, such as Community meetings,
    All Hands, Board meetings and co-located Platform meetings."""

    __record_key__: ClassVar[tuple[str, ...]] = ("title",)

    title: str = field(metadata={"description": "The event's title as the website writes it."})
    start: str | None = field(metadata={"description": "Start date as YYYY-MM-DD."})
    end: str | None = field(metadata={"description": "End date as YYYY-MM-DD."})
    url: str | None = field(metadata={"description": "The event's page on the ELIXIR website."})


class ElixirEventReader(Extractor):
    name = "elixir-event-reader"
    version = "1"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        _, main = page(document)
        table = next((t for t in main.find_all("table") if "Start date" in words(t)), None)
        if isinstance(table, Tag):
            records: list[dict[str, Any]] = []
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                link = cells[0].find("a") if cells else None
                if len(cells) < 2:
                    continue
                quote = " | ".join(words(cell) for cell in cells)
                records.append(
                    {
                        "title": quoted(words(cells[0]), quote),
                        "start": quoted(day(words(cells[1])), quote),
                        "end": located(None, "events listing"),
                        "url": quoted(urljoin(SITE, str(link["href"])) if isinstance(link, Tag) else None, quote),
                    }
                )
            return records
        heading = main.find("h1")
        when = re.search(r"Date:\s*(.+?)(?:Time zone|Location|Registration|$)", words(main))
        if not isinstance(heading, Tag) or not when:
            return []
        span = when.group(1)
        start, _, end = span.partition(" to ")
        return [
            {
                "title": quoted(words(heading), words(heading)),
                "start": quoted(day(start), span),
                "end": quoted(day(end) if end else None, span),
                "url": located(url_of(document.path), "page"),
            }
        ]
