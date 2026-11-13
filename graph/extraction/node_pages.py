import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

from biotope.extraction import Document, ExtractionError, Extractor, Schema
from bs4 import BeautifulSoup, Tag

from ._reading import rendered
from .roles import PlaceKind, RoleKind

NODE = "ELIXIR-UK"
HONORIFICS = {"Dr", "Prof", "Professor", "Mr", "Mrs", "Ms", "Miss", "Sir", "Dame"}
ORCID = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]")
GROUP_WORDS = re.compile(r"\b(Club|Community|Platform|Focus Group|Group|Fellowship|Network)\b")
TITLE_ROLE = re.compile(r"^(?P<place>.+?)\s+(?P<role>Deputy Lead|Co-lead|Lead|Coordinator|Chair)$")
NODE_ROLES = (
    (re.compile(r"Head of Node", re.I), "head_of_node"),
    (re.compile(r"Deputy Node Coordinator", re.I), "deputy"),
    (re.compile(r"Node Coordinator", re.I), "node_coordinator"),
)
GOVERNANCE_KINDS = {"Heads of Node": "head_of_node", "Coordination office": "staff"}


@dataclass(frozen=True, kw_only=True)
class NodePageRole:
    """A person's role, membership or position as an ELIXIR-UK people or activity page shows it in the page's
    structure: the title under the name, the organisation, the ORCID link, governance roles, the groups the person
    leads ('Community leadership'), the groups, clubs and projects listed on the profile, and the 'Coordination /
    leads' of an activity page. Read by code, not by a language model."""

    __record_key__: ClassVar[tuple[str, ...]] = ("person", "place", "role")

    person: str = field(metadata={"description": "The person's name without titles such as Dr or Prof."})
    role: str = field(metadata={"description": "The role as the page writes it, or 'member' for a listed group."})
    role_kind: RoleKind = field(metadata={"description": "The kind of role, as in role_statements."})
    place: str = field(metadata={"description": "The group, project, Node or body where the person holds the role."})
    place_kind: PlaceKind = field(metadata={"description": "What kind of place the role is held in."})
    affiliation: str | None = field(metadata={"description": "The person's organisation as the page writes it."})
    node: str | None = field(
        metadata={"description": "ELIXIR-UK when the person's organisation is listed as an ELIXIR-UK member, else null."}
    )
    orcid: str | None = field(metadata={"description": "The ORCID iD the profile links to."})


def text_of(tag: Tag) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())


def person_name(strings: list[str]) -> str:
    words = [word for word in strings if word not in HONORIFICS]
    return words[0] if words else ""


def record(person: str, role: str, role_kind: str, place: str, place_kind: str, quote: str, **extra: str | None) -> dict[str, Any]:
    values = {"person": person, "role": role, "role_kind": role_kind, "place": place, "place_kind": place_kind}
    values |= {"affiliation": extra.get("affiliation"), "node": extra.get("node"), "orcid": extra.get("orcid")}
    return {name: {"value": value, "quote": quote} for name, value in values.items()}


def main_of(document: Document) -> Tag:
    soup = BeautifulSoup(document.path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    main = soup.find("main")
    if not isinstance(main, Tag):
        raise ExtractionError(f"{document.path.name}: no main content")
    for tag in main.find_all(["script", "style", "svg", "noscript"]):
        tag.decompose()
    return main


def block_after(main: Tag, label: str) -> Tag | None:
    found = main.find(string=lambda value: bool(value) and value.strip() == label)
    if found is None or found.parent is None:
        return None
    block = found.parent
    while block.parent is not None and len(list(block.stripped_strings)) <= 1:
        block = block.parent
    return block


def title_roles(title: str) -> list[tuple[str, str, str, str]]:
    roles: list[tuple[str, str, str, str]] = []
    for part in (part.strip() for part in title.split(",")):
        if not part or part.lower().startswith("former"):
            continue
        node_kind = next((kind for pattern, kind in NODE_ROLES if pattern.search(part)), None)
        if node_kind:
            roles.append((part, node_kind, NODE, "node"))
        elif "Fellow" in part:
            roles.append((part, "participant", "BioFAIR" if "BioFAIR" in part else "ELIXIR-UK Fellowship", "project"))
        elif (match := TITLE_ROLE.match(part)) and GROUP_WORDS.search(match.group("place")):
            kind = {"Deputy Lead": "deputy", "Co-lead": "co_lead", "Chair": "chair", "Coordinator": "coordinator"}
            roles.append((part, kind.get(match.group("role"), "lead"), match.group("place"), "group"))
        else:
            roles.append((part, "staff", NODE, "node"))
    return roles


def card(link: Tag) -> tuple[list[str], str]:
    item = link.find_parent("li") or link
    tags = [text_of(span) for span in item.select('span[class*="term-"]')]
    strings = [value for value in item.stripped_strings if value not in tags and value not in {",", "|"}]
    return tags, strings[0] if strings else ""


class UkPeopleReader(Extractor):
    name = "uk-people-reader"
    version = "2"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        if document.path.name.startswith("activities-"):
            return self.activity(document)
        return self.person(document)

    def person(self, document: Document) -> list[dict[str, Any]]:
        main = main_of(document)
        heading = main.find("h1")
        if not isinstance(heading, Tag) or not isinstance(heading.parent, Tag) or not isinstance(heading.parent.parent, Tag):
            raise ExtractionError(f"{document.path.name}: no profile heading")
        header = heading.parent.parent
        name = person_name([value for value in heading.stripped_strings])
        members = [text_of(link) for link in header.find_all("a", href=re.compile(r"/members/"))]
        others = [text_of(link) for link in header.find_all("a", href=re.compile(r"/collaborator/"))]
        spans = [text_of(span) for span in header.find_all("span") if span.find(string=True, recursive=False)]
        title = next((value for value in spans if value and value not in HONORIFICS and value != name), None)
        plain = [value for value in header.stripped_strings if value not in HONORIFICS and value not in (name, title)]
        affiliation = next(iter(members or plain or others), None)
        orcid_link = main.find("a", href=re.compile(r"orcid\.org/"))
        orcid = ORCID.search(str(orcid_link.get("href"))) if isinstance(orcid_link, Tag) else None
        node = NODE if members else None
        quote = rendered(header)
        extra = {"affiliation": affiliation, "node": node, "orcid": orcid.group(0) if orcid else None}
        if name in ("", "Our people"):
            return []
        records = [record(name, role, kind, place, place_kind, quote, **extra) for role, kind, place, place_kind in title_roles(title or "")]
        for link in main.select('.governance-tags-container a[href*="/governance-role/"]'):
            body = text_of(link)
            kind = GOVERNANCE_KINDS.get(body, "member")
            place = NODE if kind != "member" else f"{body} ({NODE})"
            records.append(record(name, body, kind, place, "node" if kind != "member" else "governance_body", rendered(link), **extra))
        leading = block_after(main, "Community leadership")
        led: set[Tag] = set(leading.select("a.gspbgrid_item_link")) if leading else set()
        for link in main.select("a.gspbgrid_item_link"):
            href = str(link.get("href") or "")
            if "/activities/" not in href:
                continue
            tags, title_text = card(link)
            if not title_text:
                continue
            if link in led:
                records.append(record(name, "Community leadership", "lead", title_text, "group", rendered(leading or link), **extra))
            else:
                kind = "participant" if "Fellowship" in tags else "member"
                records.append(record(name, "member", kind, title_text, "group", rendered(link.find_parent("li") or link), **extra))
        for link in main.find_all("a", href=re.compile(r"elixiruknode\.org/project/")):
            box = link.parent if isinstance(link.parent, Tag) else link
            heading_tag = box.find("h3")
            if not isinstance(heading_tag, Tag):
                continue
            project = text_of(heading_tag)
            records.append(record(name, "participant", "participant", project, "project", rendered(box), **extra))
        if not records and node:
            records.append(record(name, "member", "member", NODE, "node", quote, **extra))
        return list({(r["person"]["value"], r["place"]["value"], r["role"]["value"]): r for r in records}.values())

    def activity(self, document: Document) -> list[dict[str, Any]]:
        main = main_of(document)
        heading = main.find(["h1", "h2"])
        if not isinstance(heading, Tag):
            raise ExtractionError(f"{document.path.name}: no activity heading")
        place = text_of(heading)
        block = block_after(main, "Coordination / leads")
        if block is None:
            return []
        records: list[dict[str, Any]] = []
        for link in block.find_all("a", href=re.compile(r"/people/")):
            container = link.parent if isinstance(link.parent, Tag) else link
            while isinstance(container.parent, Tag) and len([v for v in container.stripped_strings if v not in HONORIFICS]) < 2:
                container = container.parent
            strings = [value for value in container.stripped_strings if value not in HONORIFICS and value != "Coordination / leads"]
            if not strings:
                continue
            person, affiliation = strings[0], (strings[1] if len(strings) > 1 else None)
            records.append(record(person, "Coordination / leads", "lead", place, "group", rendered(block), affiliation=affiliation))
        return records
