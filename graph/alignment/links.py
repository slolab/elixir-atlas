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
    published: str | None = None
    modified: str | None = None


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
    basis: str = "stated"
    quote: str | None = None


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
    join_url: str | None = None
    joining: str | None = None
    programme: str | None = None
    period_status: str | None = None
    recent_activity: tuple[str, ...] = ()
    leaders: tuple[str, ...] = ()
    limits: tuple[str, ...] = ()
    scope: str | None = None
    latest_own_activity: str | None = None
    latest_activity: str | None = None


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
    tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutputLink:
    output_id: str
    authors: tuple[tuple[str, int, str, str], ...]
    initiatives: tuple[Pair, ...]
    plan_items: tuple[Pair, ...]
    url: str | None
    creators: int | None = None


Linked = tuple[str, str, str]


@dataclass(frozen=True)
class CatalogueLink:
    item_id: str
    initiatives: tuple[Linked, ...]
    nodes: tuple[Pair, ...]
    topics: tuple[str, ...]
    people: tuple[Pair, ...]
    provider: str | None
    recommended_by: tuple[str, ...] = ()
    collections: tuple[str, ...] = ()
    collections_unnamed: int = 0


@dataclass(frozen=True)
class ParticipationLink:
    organisation_id: str
    initiative_id: str
    located: Located


@dataclass(frozen=True)
class BecameLink:
    source: str
    target: str
    date: str | None
    evidence: str | None
    located: Located


@dataclass(frozen=True)
class ResourceRecord:
    resource_id: str
    name: str
    kind: str
    url: str | None
    tools: tuple[Pair, ...]


@dataclass(frozen=True)
class RecommendationLink:
    initiative_id: str
    resource_id: str
    located: Located
    evidence: str | None


@dataclass(frozen=True)
class EventLink:
    event_id: str
    url: str | None
    initiatives: tuple[Linked, ...]


@dataclass(frozen=True)
class InvolvementRecord:
    person_id: str
    initiative_id: str
    leadership: bool
    roles: tuple[str, ...]
    plan_items: tuple[str, ...]
    outputs: tuple[str, ...]
    tools: tuple[str, ...]
    nodes: tuple[str, ...]
    organisations: tuple[str, ...]
    bases: tuple[str, ...]
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class NodeInvolvementRecord:
    node_id: str
    initiative_id: str
    bases: tuple[str, ...]
    listed_on_own_page: bool
    initiative_kind: str
    period: str | None
    period_status: str | None
    beneficiaries: tuple[str, ...]
    people: tuple[str, ...]
    node_site: str | None
    limits: str
    plan_summary: str | None
    leads_plan_items: tuple[str, ...]
    works_on_plan_items: tuple[str, ...]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class SharedWork:
    source: str
    target: str
    via: str
    item: str
    item_id: str
    source_url: str | None


@dataclass(frozen=True)
class PlanLinkRecord:
    source: str
    target: str
    direction: str
    item: str | None
    item_id: str | None
    linked_item: str | None
    linked_item_id: str | None
    relation: str
    quote: str | None
    located: Located
