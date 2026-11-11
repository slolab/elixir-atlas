import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Literal

from biotope.extraction import Document, ExtractionError, Extractor, Schema
from bs4 import BeautifulSoup, Tag

SECTIONS = {"coordinator": "coordinator", "participants": "participant", "partners": "partner"}


@dataclass(frozen=True, kw_only=True)
class CordisProject:
    """An EU-funded project as its CORDIS fact sheet states it: grant, dates, costs and coordinator. One record
    per fact sheet."""

    grant_id: str = field(metadata={"description": "Grant agreement ID."})
    acronym: str = field(metadata={"description": "Project acronym as the fact sheet gives it."})
    title: str | None = field(metadata={"description": "Project title as the fact sheet gives it."})
    start: str | None = field(metadata={"description": "Start date as YYYY-MM-DD."})
    end: str | None = field(metadata={"description": "End date as YYYY-MM-DD."})
    total_cost_eur: float | None = field(metadata={"description": "Total cost of the project in euro."})
    eu_contribution_eur: float | None = field(metadata={"description": "EU contribution to the project in euro."})
    coordinator: str | None = field(metadata={"description": "Coordinating organisation, as CORDIS names it."})
    objective: str | None = field(metadata={"description": "The project's objective text from the fact sheet."})


@dataclass(frozen=True, kw_only=True)
class CordisParticipant:
    """An organisation in an EU-funded project as its CORDIS fact sheet lists it: the coordinator, participants
    and associated partners, with country, net EU contribution and total cost. One record per organisation."""

    __record_key__: ClassVar[tuple[str, ...]] = ("organisation", "participation", "participation_ended")

    grant_id: str = field(metadata={"description": "Grant agreement ID of the project."})
    organisation: str = field(metadata={"description": "The organisation's legal name as CORDIS lists it."})
    country: str | None = field(metadata={"description": "Country CORDIS gives for the organisation."})
    participation: Literal["coordinator", "participant", "partner"] = field(
        metadata={
            "description": "The CORDIS section listing it: coordinator, participant (beneficiary) or partner "
            "(associated partner, which receives no EU contribution)."
        }
    )
    participation_ended: bool = field(
        metadata={"description": "True when CORDIS marks the organisation's participation as ended."}
    )
    net_eu_contribution_eur: float | None = field(
        metadata={"description": "Net EU contribution to this organisation in euro, as listed; null when none is listed."}
    )
    total_cost_eur: float | None = field(
        metadata={"description": "Total cost of this organisation's participation in euro, as listed."}
    )
    activity_type: str | None = field(metadata={"description": "CORDIS activity type of the organisation."})


def euro(text: str) -> float | None:
    match = re.search(r"€\s*([\d\s ]+(?:,\d+)?)", text)
    if not match:
        return None
    return float(re.sub(r"[\s ]", "", match.group(1)).replace(",", "."))


def soup_of(document: Document) -> BeautifulSoup:
    soup = BeautifulSoup(document.path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    if not soup.select(".c-project-info__label"):
        raise ExtractionError(f"{document.path.name}: not a CORDIS fact sheet")
    return soup


def located(value: object, locator: str) -> dict[str, Any]:
    return {"value": value, "locator": locator}


def grant_of(soup: BeautifulSoup) -> str:
    match = re.search(r"Grant agreement ID:\s*(\d+)", soup.get_text(" ", strip=True))
    if not match:
        raise ExtractionError("no grant agreement ID")
    return match.group(1)


class CordisProjectReader(Extractor):
    name = "cordis-project-reader"
    version = "1"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        soup = soup_of(document)
        info: dict[str, str] = {}
        for label in soup.select(".c-project-info__label"):
            parent = label.parent
            if isinstance(parent, Tag):
                key = label.get_text(" ", strip=True)
                info[key] = " ".join(parent.get_text(" ", strip=True).removeprefix(key).split())
        title = soup.select_one("h1")
        acronym = soup.select_one("[class*=acronym]")
        objective = soup.find("h2", string=re.compile("Objective"))
        body = objective.find_next_sibling() if isinstance(objective, Tag) else None
        objective_text = body.get_text(" ", strip=True) if isinstance(body, Tag) else None
        coordinator = soup.select_one(".c-organisation .c-part-info__title")
        text = soup.get_text(" ", strip=True)
        total = re.search(r"Total cost The total amount of money.*?(€\s*[\d\s\u00a0]+(?:,\d+)?)", text, re.DOTALL)
        contribution = re.search(r"EU contribution Amount of money.*?(€\s*[\d\s\u00a0]+(?:,\d+)?)", text, re.DOTALL)
        return [
            {
                "grant_id": located(grant_of(soup), "Project Information"),
                "acronym": located(acronym.get_text(" ", strip=True) if acronym else document.path.name, "acronym"),
                "title": located(title.get_text(" ", strip=True) if title else None, "title"),
                "start": located(self.date(info.get("Start date")), "Start date"),
                "end": located(self.date(info.get("End date")), "End date"),
                "total_cost_eur": located(euro(total.group(1)) if total else None, "Total cost"),
                "eu_contribution_eur": located(euro(contribution.group(1)) if contribution else None, "EU contribution"),
                "coordinator": located(
                    next(coordinator.stripped_strings, None) if coordinator else None, "Coordinator"
                ),
                "objective": located(" ".join((objective_text or "").split()) or None, "Objective"),
            }
        ]

    def date(self, value: str | None) -> str | None:
        if not value:
            return None
        return datetime.strptime(value.strip(), "%d %B %Y").date().isoformat()


class CordisParticipantReader(Extractor):
    name = "cordis-participant-reader"
    version = "1"

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        soup = soup_of(document)
        grant = grant_of(soup)
        records: list[dict[str, Any]] = []
        for block in soup.select(".c-organisation"):
            heading = block.find_previous("h3")
            section = heading.get_text(" ", strip=True).split(" ")[0].lower() if isinstance(heading, Tag) else ""
            if section not in SECTIONS:
                raise ExtractionError(f"{document.path.name}: organisation outside a known section ({section})")
            title = block.select_one(".c-part-info__title")
            names = list(title.stripped_strings) if title else []
            ended = "Participation ended" in names
            names = [name for name in names if name != "Participation ended"]
            if not names:
                raise ExtractionError(f"{document.path.name}: organisation without a name")
            values = self.values(block)
            where = f"{heading.get_text(' ', strip=True) if isinstance(heading, Tag) else ''}: {names[0]}"
            records.append(
                {
                    "grant_id": located(grant, where),
                    "organisation": located(names[0], where),
                    "country": located(names[1] if len(names) > 1 else None, where),
                    "participation": located(SECTIONS[section], where),
                    "participation_ended": located(ended, where),
                    "net_eu_contribution_eur": located(euro(values.get("Net EU contribution", "")), where),
                    "total_cost_eur": located(euro(values.get("Total cost", "")), where),
                    "activity_type": located(values.get("Activity type"), where),
                }
            )
        if not records:
            raise ExtractionError(f"{document.path.name}: no organisations listed")
        return records

    def values(self, block: Tag) -> dict[str, str]:
        values: dict[str, str] = {}
        for subtitle in block.select(".c-part-info__subtitle"):
            label = next(subtitle.stripped_strings, "")
            content = subtitle.find_next_sibling(class_="c-part-info__content")
            if isinstance(content, Tag) and label not in values:
                values[label] = content.get_text(" ", strip=True)
        return values
