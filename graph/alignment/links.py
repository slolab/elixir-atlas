from dataclasses import dataclass

Pair = tuple[str, str]


@dataclass(frozen=True)
class Located:
    document_id: str | None
    url: str | None
    retrieved_at: str | None


@dataclass(frozen=True)
class DocumentInfo:
    document_id: str
    path: str
    url: str | None
    retrieved_at: str | None
    source: str | None
    content_type: str | None


@dataclass(frozen=True)
class TopicEntry:
    topic_id: str
    label: str
    uri: str


@dataclass(frozen=True)
class EdgeLink:
    source: str
    target: str
    as_written: str
    located: Located
    role: str | None = None


@dataclass(frozen=True)
class InitiativeRecord:
    initiative_id: str
    name: str
    acronym: str | None
    kind: str
    family: str
    aliases: tuple[str, ...]
    pages: tuple[str, ...]
    identity_basis: tuple[str, ...]
    start: str | None
    end: str | None
    status: str | None
    summary: str | None
    outcomes: tuple[str, ...]
    contacts: tuple[str, ...]
    grant_id: str | None
    total_cost_eur: float | None
    eu_contribution_eur: float | None


@dataclass(frozen=True)
class StatementLink:
    statement_id: str
    initiative_id: str
    evidence: str | None
    located: Located
    topics: tuple[str, ...]


@dataclass(frozen=True)
class RoleLink:
    person_id: str
    initiative_id: str
    work_item: str | None
    role_kind: str
    funding: str
    evidence: str | None
    located: Located


@dataclass(frozen=True)
class PlanItemRecord:
    plan_item_id: str
    initiative_id: str
    kind: str
    code: str | None
    label: str
    description: str | None
    parent: str | None
    date: str | None
    date_as_written: str | None
    date_statements: tuple[str, ...]
    status: str
    leads: tuple[str, ...]
    participants: tuple[str, ...]
    effort: str | None
    link: str | None
    sources: tuple[str, ...]
    evidence: str | None
    topics: tuple[str, ...]


@dataclass(frozen=True)
class OutputLink:
    output_id: str
    authors: tuple[tuple[str, int, str, str], ...]
    initiatives: tuple[Pair, ...]
    plan_items: tuple[Pair, ...]
    url: str | None


@dataclass(frozen=True)
class CatalogueLink:
    item_id: str
    initiatives: tuple[Pair, ...]
    nodes: tuple[Pair, ...]
    topics: tuple[str, ...]
    people: tuple[Pair, ...]
    provider: str | None


@dataclass(frozen=True)
class ParticipationLink:
    organisation_id: str
    initiative_id: str
    located: Located
