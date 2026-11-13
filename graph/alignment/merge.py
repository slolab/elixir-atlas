import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from .initiatives import InitiativeIdentity
from .keys import plain
from .links import InitiativeRecord, PlanItemRecord
from .names import ascii_fold, digest, slug
from .reviews import Review, agreed_date, dates_agree, months, review

Decided = Callable[[str], str | None]

PROGRESS = ("done", "delayed", "ongoing", "open", "planned")


@dataclass(frozen=True)
class Stated:
    url: str | None
    coverage: str
    primary: bool
    start: str | None
    end: str | None
    status: str
    summary: str | None
    outcomes: tuple[str, ...]
    contacts: tuple[str, ...]


@dataclass(frozen=True)
class Funded:
    url: str | None
    grant_id: str
    start: str | None
    end: str | None
    objective: str | None
    total_cost_eur: float | None
    eu_contribution_eur: float | None


@dataclass(frozen=True)
class PlannedItem:
    initiative_id: str
    initiative_name: str
    kind: str
    code: str | None
    label: str
    description: str | None
    parent: str | None
    date: str | None
    date_as_written: str | None
    status: str
    leads: tuple[str, ...]
    participants: tuple[str, ...]
    effort: str | None
    link: str | None
    url: str | None
    evidence: str | None
    topics: tuple[str, ...]
    month_start: str | None = None


def option(value: str, urls: list[str | None]) -> str:
    known = sorted({url for url in urls if url})
    return f"{value} | {', '.join(known[:3])}" if known else value


def date_conflict(subject: str, name: str, prop: str, values: list[tuple[str, str | None]]) -> Review | None:
    if dates_agree([value for value, _ in values]):
        return None
    urls: dict[str, list[str | None]] = defaultdict(list)
    for value, url in values:
        urls[value].append(url)
    return review(
        "value_conflict",
        f"Sources give different {'dates' if prop == 'date' else f'{prop} dates'} for {name}, more than a month apart. Which is right?",
        [subject],
        [name],
        [option(value, urls[value]) for value in sorted(urls)],
        prop,
    )


def chosen(conflict: Review | None, decided: Decided) -> str | None:
    value = decided(conflict.review_id) if conflict else None
    return value if value and months(value) is not None else None


def merge_initiative(
    identity: InitiativeIdentity, stated: list[Stated], funded: Funded | None, decided: Decided
) -> tuple[InitiativeRecord, list[Review]]:
    reviews: list[Review] = []
    described = [s for s in stated if s.coverage == "described"]
    primary = [s for s in described if s.primary] or described
    dates: dict[str, str | None] = {}
    for prop in ("start", "end"):
        values = [(value, s.url) for s in stated if (value := getattr(s, prop))]
        if funded and (value := getattr(funded, prop)):
            values.append((value, funded.url))
        own = [value for s in primary if (value := getattr(s, prop))]
        dates[prop] = agreed_date(own) if own else agreed_date([value for value, _ in values])
        compared = [(f"{value}-12" if prop == "end" and re.fullmatch(r"\d{4}", value) else value, url) for value, url in values]
        if conflict := date_conflict(identity.initiative_id, identity.name, prop, compared):
            reviews.append(conflict)
            dates[prop] = chosen(conflict, decided) or dates[prop]
    statuses = [s.status for s in primary if s.status != "not_stated"]
    statuses = statuses or [s.status for s in described if s.status != "not_stated"]
    status = Counter(statuses).most_common(1)[0][0] if statuses else None
    summary = next((s.summary for s in primary if s.summary), None)
    summary = summary or (funded.objective if funded else None)
    summary = summary or next((s.summary for s in stated if s.summary), None)
    outcomes = tuple(dict.fromkeys(o for s in described for o in s.outcomes))
    contacts = tuple(dict.fromkeys(c for s in stated for c in s.contacts))
    record = InitiativeRecord(
        initiative_id=identity.initiative_id,
        name=identity.name,
        acronym=identity.acronym,
        kind=identity.kind,
        family=identity.family,
        aliases=identity.aliases,
        pages=identity.pages,
        identity_basis=identity.identity_basis,
        start=dates["start"],
        end=dates["end"],
        status=status,
        summary=summary,
        outcomes=outcomes,
        contacts=contacts,
        grant_id=funded.grant_id if funded else None,
        total_cost_eur=funded.total_cost_eur if funded else None,
        eu_contribution_eur=funded.eu_contribution_eur if funded else None,
    )
    return record, reviews


def code_key(code: str | None) -> str | None:
    if not code:
        return None
    key = re.sub(r"[^a-z0-9.]+", "", ascii_fold(code).lower()).strip(".")
    for long, short in (("workpackage", "wp"), ("task", "t"), ("deliverable", "d"), ("milestone", "m")):
        key = key.replace(long, short)
    return key or None


UNIQUE_CODE = re.compile(r"^(wp|d|m|ms)\d|\d\.\d")


def scoped_code(code: str | None, parent: str | None) -> str | None:
    key = code_key(code)
    if key is None or UNIQUE_CODE.search(key) or not parent:
        return key
    return f"{code_key(parent) or plain(parent)}/{key}"


def plan_key(item: PlannedItem) -> tuple[str, str]:
    code = scoped_code(item.code, item.parent)
    return item.initiative_id, f"{item.kind}:{code}" if code else f"{item.kind}:{plain(item.label)}"


def project_month(written: str | None, start: str | None) -> str | None:
    match = re.fullmatch(r"\s*M\s?(\d{1,3})\s*", written or "")
    begin = months(start) if start and len(start.split("-")) > 1 else None
    if not match or begin is None:
        return None
    point = begin + int(match.group(1)) - 1
    year, month = divmod(point - 1, 12)
    return f"{year:04d}-{month + 1:02d}"


def lists_code(item: PlannedItem) -> bool:
    text = (item.evidence or "").split(": ", 1)[-1]
    return bool(item.code and re.match(rf"\W*{re.escape(item.code.strip())}\b", text, re.I))


def label_words(label: str) -> set[str]:
    return {word for word in plain(label).split() if len(word) > 3}


def merge_plan_items(
    items: list[PlannedItem], decided: Decided, start: str | None
) -> tuple[PlanItemRecord, list[Review], int]:
    first = items[0]
    initiative_id, key = plan_key(first)
    plan_item_id = f"plan:{initiative_id.removeprefix('initiative:')}/{slug(key)}"
    if len(plan_item_id) > 160:
        plan_item_id = f"plan:{initiative_id.removeprefix('initiative:')}/{digest(key)}"
    labels = Counter(item.label for item in items)
    coded = {item.label for item in items if lists_code(item)}
    label = sorted(labels.items(), key=lambda pair: (pair[0] not in coded, -pair[1], pair[0]))[0][0]
    total = len(items)
    items = [item for item in items if lists_code(item) or label_words(item.label) & label_words(label) or item.label == label]
    values = [(item.date, item.url) for item in items if item.date]
    reviews: list[Review] = []
    date = agreed_date([v for v, _ in values if v])
    if not values:
        date = next((found for item in items if (found := project_month(item.date_as_written, item.month_start or start))), None)
    if conflict := date_conflict(plan_item_id, f"{label} ({first.initiative_name})", "date", [(v, u) for v, u in values if v]):
        reviews.append(conflict)
        date = chosen(conflict, decided)
    statuses = {item.status for item in items}
    status = next((s for s in PROGRESS if s in statuses), "not_stated")
    record = PlanItemRecord(
        plan_item_id=plan_item_id,
        initiative_id=initiative_id,
        kind=first.kind,
        code=next((item.code for item in items if item.code), None),
        label=label,
        description=next((item.description for item in items if item.description), None),
        parent=next((item.parent for item in items if item.parent), None),
        date=date,
        date_as_written=next((item.date_as_written for item in items if item.date_as_written), None),
        date_statements=tuple(dict.fromkeys(f"{v} | {u or 'unknown source'}" for v, u in values if v)),
        status=status,
        leads=tuple(dict.fromkeys(lead for item in items for lead in item.leads)),
        participants=tuple(dict.fromkeys(p for item in items for p in item.participants)),
        effort=next((item.effort for item in items if item.effort), None),
        link=next((item.link for item in items if item.link), None),
        sources=tuple(dict.fromkeys(item.url for item in items if item.url)),
        evidence=next((item.evidence for item in items if item.evidence), None),
        topics=tuple(dict.fromkeys(t for item in items for t in item.topics)),
    )
    return record, reviews, total - len(items)
