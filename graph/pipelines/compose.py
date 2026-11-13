import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import TypeVar
from urllib.parse import urljoin

from biotope.graph import Evidence, RunContext, SourceRecord

from ..alignment.catalogues import collection_name, names_by_count, zenodo_record_id
from ..alignment.derived import NOT_SHARING, SHARING_LEADERS, Derived, limits
from ..alignment.derived import People as Persons
from ..alignment.initiatives import Claim, InitiativeIdentity, Initiatives, resolve_initiatives
from ..alignment.keys import acronym_key, family, group_key, plain, url_key
from ..alignment.links import (
    BecameLink,
    CatalogueLink,
    Located,
    DocumentInfo,
    EdgeLink,
    EventLink,
    InitiativeRecord,
    Linked,
    OutputLink,
    ParticipationLink,
    PlanItemRecord,
    PlanLinkRecord,
    RecommendationLink,
    ResourceRecord,
    RoleLink,
    StatementLink,
    TopicEntry,
)
from ..alignment.merge import (
    Funded,
    PlannedItem,
    Stated,
    code_key,
    label_words,
    merge_initiative,
    merge_plan_items,
    option,
    plan_key,
    scoped_code,
)
from ..alignment.names import digest, display_name, is_person_name, name_key, slug
from ..alignment.nodes import BY_ID, CODES, NODES, resolve_code_prefix, resolve_node
from ..alignment.organisations import resolve_organisations
from ..alignment.people import Mention, People, email_of, orcid_of, resolve_people
from ..alignment.registry import Entry, Phrases, entry_id, full_name, page_url_key, priority, registry_claims
from ..alignment.reviews import Review, review, review_id
from ..mappings.catalogues import (
    ELIXIR_EVENTS,
    EVENTS,
    F1000_OUTPUTS,
    MATERIALS,
    REVIEW_PAPERS,
    SOURCE_DOCUMENTS,
    TOOLS,
    TOPICS,
    ZENODO_OUTPUTS,
)
from ..mappings.derived import INVOLVED_IN, NODE_INVOLVED_IN, PLAN_LINKED_TO, SHARES_WORK_WITH
from ..mappings.entities import ELIXIR_NODES, ORGANISATIONS, PEOPLE, REVIEW_ITEMS
from ..mappings.initiatives import BECAME, INITIATIVES, PART_OF, PARTICIPATIONS, RELATED_TO, SOURCE_STATEMENTS, TAKES_PART_IN
from ..mappings.people import AFFILIATED_WITH, CANDIDATES, HOLDS_ROLE, IN_NODE, WORKS_ON_PLAN_ITEM
from ..mappings.plans import PLAN_ITEMS
from ..mappings.resources import RECOMMENDS, RESOURCES
from ..sources.catalogues.biotools.loader import load as load_biotools
from ..sources.catalogues.biotools.schema import BiotoolsTool
from ..sources.catalogues.biotools_domains.loader import load as load_domains
from ..sources.catalogues.biotools_domains.schema import BiotoolsDomain
from ..sources.catalogues.europepmc_reviews.loader import load as load_reviews
from ..sources.catalogues.f1000_items.loader import load as load_f1000
from ..sources.catalogues.f1000_items.schema import F1000Item
from ..sources.catalogues.tess_events.loader import load as load_events
from ..sources.catalogues.tess_facets.loader import load as load_facets
from ..sources.catalogues.tess_materials.loader import load as load_materials
from ..sources.catalogues.zenodo_records.loader import load as load_zenodo
from ..sources.corrections_csv.corrections_csv_corrections.loader import load as load_corrections
from ..sources.corrections_csv.corrections_csv_corrections.schema import Correction
from ..sources.cordis_participants_jsonl.records.loader import load as load_participants
from ..sources.cordis_projects_jsonl.records.loader import load as load_projects
from ..sources.data_sources_scraping_jsonl.scraping_index.loader import load as load_index
from ..sources.election_candidates_jsonl.records.loader import load as load_candidates
from ..sources.election_candidates_jsonl.records.schema import ElectionCandidateRow
from ..sources.elixir_events_jsonl.records.loader import load as load_elixir_events
from ..sources.elixir_events_jsonl.records.schema import ElixirEventRow
from ..sources.elixir_pages_jsonl.records.loader import load as load_pages
from ..sources.elixir_pages_jsonl.records.schema import ElixirPageRow
from ..sources.group_directory_jsonl.records.loader import load as load_directory
from ..sources.group_directory_jsonl.records.schema import GroupDirectoryRow
from ..sources.initiative_statements_jsonl.records.loader import load as load_statements
from ..sources.initiative_statements_jsonl.records.schema import InitiativeStatementRow
from ..sources.node_page_roles_jsonl.node_page_roles_jsonl_node_page_roles.loader import load as load_node_roles
from ..sources.node_page_roles_jsonl.node_page_roles_jsonl_node_page_roles.schema import NodePageRoleRow
from ..sources.perun.export.loader import load as load_perun
from ..sources.perun.export_2.loader import load as load_perun_2
from ..sources.plan_items_jsonl.records.loader import load as load_plan_items
from ..sources.plan_items_jsonl.records.schema import PlanItemRow
from ..sources.plan_links_jsonl.records.loader import load as load_plan_links
from ..sources.plan_links_jsonl.records.schema import PlanLinkRow
from ..sources.recommendations_jsonl.records.loader import load as load_recommendations
from ..sources.recommendations_jsonl.records.schema import RecommendationRow
from ..sources.role_statements_jsonl.records.loader import load as load_roles
from ..sources.review_decisions_csv.decisions.loader import load as load_decisions
from ..sources.review_decisions_csv.decisions.schema import ReviewDecision
from ..sources.role_statements_jsonl.records.schema import RoleStatementRow

NODE_LIST_PAGE = "elixir-europe.org/about-us/who-we-are/nodes"
LEADS = frozenset({"lead", "co_lead"})
WORK_LEADS = frozenset({"work_package_lead", "task_lead", "lead", "co_lead"})
NODE_ROLES = frozenset({"head_of_node", "node_coordinator"})
WORK_ITEM_CODE = re.compile(r"\b((?:WP|Work ?Package|T|Task|Activity|D|M)\s?\d+(?:\.\d+)*)", re.I)
PARTNER_PREFIX = re.compile(r"^\s*[A-Z]{2,4}-[\w.&-]+\s*[-–:,]\s*")
HEADING_ROLE = re.compile(r"\b(leads?|leaders?|co-leads?|chairs?|co-chairs?|coordinators?|directors?)\b", re.I)
GENERIC_BODY = re.compile(
    r"\b(general assembly|management (team|board|committee)|advisory (board|committee)|steering (committee|group)|"
    r"executive (board|committee)|heads of nodes|board|committee|council|\b(SAB|EAB|STAB|IAC|PMT|GA)\b)",
    re.I,
)
MAX_WORK_LEADS = 3
REGISTRY_KINDS = frozenset({"community", "platform", "focus_group"})
MERGED_KINDS = {"programme_project": "commissioned_service", "implementation_study": "commissioned_service"}
SCIENTIFIC_PROGRAMME = "elixir-europe.org/how-we-work/scientific-programme/"
PROGRAMME = "2024-28 Scientific Programme"
SNAPSHOT_MONTH = "2026-11"
SNAPSHOT_DATE = "2026-11-11"
ACTIVITY_ITEMS = 8
SCOPE_PLAN_KINDS = frozenset({"goal", "objective", "action", "work_package", "output", "practice", "activity"})
AREA_PAGE = re.compile(r"elixir-europe\.org/(?:how-we-work/scientific-programme|internal-projects/commissioned-services)/science/[^/]+$")
LEAD_NODE_ROLES = frozenset({"lead", "co_lead", "coordinator"})
DOMAIN_COMMUNITY = entry_id("Systems Biology", "community")
TOOL_RESOURCES = frozenset({"tool", "database"})
WORK_PACKAGE_NUMBER = re.compile(r"^\s*(?:WP|Work ?Package|D|M|MS|T|Task)\s?(\d+)\b", re.I)
ADVISORY_ROLE = re.compile(r"advis|\bexternal\b|\b(SAB|EAB|STAB)\b", re.I)
INFRASTRUCTURE_NAMES = ("elixir", "elixir europe", "elixir hub")
FUNDING_WORDS = re.compile(r"\b(fund|funded|funding|grant|financ|paid|salar|in[- ]kind|sponsor)", re.I)
ACRONYM_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{3,}")
NODE_PROJECT_LISTINGS = frozenset({"node-uk", "node-germany", "node-czech", "node-luxembourg", "node-netherlands", "node-norway"})
SERIES = re.compile(r"^(.*?)\|\s*(WP\s?\d+)\s*\|", re.I)
SERIES_BASES = frozenset({"linked", "deliverable", "grant"})
GROUP_QUALIFIER = re.compile(r"community|platform|focus group|elixir", re.I)
DELIVERABLE_CODE = re.compile(r"\b([DM]\s?\d+\.\d+)\b")
PLAN_PROJECT_KINDS = frozenset({"work_package", "task", "deliverable", "milestone"})
EU_PROJECT_LISTING = "elixir-europe.org/about-us/how-funded/eu-projects"
LEAD_CLAIMS = frozenset({"lead", "co_lead", "chair", "coordinator"})
UNCONFIRMED_LEAD = "unconfirmed_lead"
INTERNATIONAL_NODES = frozenset({"node:embl-ebi", "node:hub"})
CORRECTED = Located(None, None, None)
GROUP_WORDS = (
    ("community", "community"),
    ("platform", "platform"),
    ("focus group", "focus_group"),
    ("task force", "task_force"),
)


@dataclass
class Collected:
    evidence: dict[str, set[Evidence]] = field(default_factory=lambda: defaultdict(set))
    reviews: dict[str, Review] = field(default_factory=dict[str, Review])
    edges: dict[str, dict[str, SourceRecord[EdgeLink]]] = field(default_factory=lambda: defaultdict(dict))
    counts: Counter[str] = field(default_factory=Counter[str])

    def cite(self, key: str, evidence: Iterable[Evidence]) -> None:
        self.evidence[key].update(evidence)

    def cited(self, *keys: str, limit: int = 200) -> tuple[Evidence, ...]:
        found = {e for key in keys for e in self.evidence.get(key, set())}
        return tuple(sorted(found, key=lambda e: (e.artifact, e.location))[:limit])

    def add_review(self, item: Review | None) -> None:
        if item is not None:
            self.reviews.setdefault(item.review_id, item)

    def edge(self, kind: str, link: EdgeLink, evidence: tuple[Evidence, ...]) -> None:
        key = digest(link.source, link.target, link.located.document_id or "", link.role or "", link.basis)
        if key not in self.edges[kind]:
            self.edges[kind][key] = SourceRecord(link, evidence)
        if kind in ("takes_part_in", "in_node"):
            node = link.source if kind == "takes_part_in" else link.target
            self.cite(node, evidence)


@dataclass
class Decisions:
    rows: dict[str, SourceRecord[ReviewDecision]]
    used: set[str] = field(default_factory=set[str])

    def __call__(self, identifier: str) -> str | None:
        row = self.rows.get(identifier)
        if row is None:
            return None
        self.used.add(identifier)
        return row.value.decision

    def same(self, kind: str, candidates: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(left, right) for left, right in candidates if (self(review_id(kind, [left, right])) or "").lower() == "same"]

    def resolved(self, item: Review) -> Review:
        decision = self(item.review_id)
        return replace(item, status="resolved", decision=decision) if decision else item

    def evidence(self, identifier: str) -> tuple[Evidence, ...]:
        row = self.rows.get(identifier)
        return row.evidence if row else ()


@dataclass
class Documents:
    info: dict[str, SourceRecord[DocumentInfo]]
    redirects: dict[str, str]
    used: set[str] = field(default_factory=set[str])

    def located(self, path: str) -> Located:
        record = self.info.get(path)
        if record is None:
            return Located(None, None, None)
        self.used.add(path)
        return Located(record.value.document_id, record.value.url, record.value.retrieved_at)

    def url(self, path: str) -> str | None:
        record = self.info.get(path)
        return record.value.url if record else None

    def superseded(self, read: set[str]) -> set[str]:
        latest: dict[str, tuple[str, str]] = {}
        for path, record in self.info.items():
            if path in read and (key := page_identity(record.value.url)):
                stamp = (record.value.retrieved_at or "", path)
                latest[key] = max(latest.get(key, stamp), stamp)
        newest = {path for _, path in latest.values()}
        return {path for path in read if path in self.info and page_identity(self.info[path].value.url) and path not in newest}


Row = TypeVar(
    "Row",
    InitiativeStatementRow,
    RoleStatementRow,
    PlanItemRow,
    PlanLinkRow,
    GroupDirectoryRow,
    ElixirPageRow,
    ElectionCandidateRow,
    ElixirEventRow,
    RecommendationRow,
)


def page_identity(url: str | None) -> str | None:
    return url.split("#", 1)[0].rstrip("/") if url else None


def kept(context: RunContext, rows: list[SourceRecord[Row]], dropped: set[str], policy: str) -> list[SourceRecord[Row]]:
    found: list[SourceRecord[Row]] = []
    for row in rows:
        if row.value.document in dropped:
            context.exclude(policy, row.evidence)
        else:
            found.append(row)
    return found


def latest(context: RunContext, documents: Documents, rows: list[SourceRecord[Row]]) -> list[SourceRecord[Row]]:
    return kept(context, rows, documents.superseded({row.value.document for row in rows}), "superseded_snapshot")


def quote(record: SourceRecord[object]) -> str | None:
    return record.evidence[1].location if len(record.evidence) > 1 else None


def absolute(base: str | None, link: str) -> str:
    link = link.strip().strip("<>")
    return urljoin(base, link) if base and link.startswith("/") else link


def guess_kind(place: str, place_kind: str) -> str:
    if place_kind not in ("group", "governance_body"):
        return "other_project"
    text = plain(place)
    for word, kind in GROUP_WORDS:
        if word in text:
            return kind
    if place_kind == "governance_body":
        return "governance_group"
    if place_kind == "group":
        return "working_group"
    return "other_project"


def period_status(start: str | None, end: str | None) -> str | None:
    if not end:
        return None
    if f"{end}-12-31"[:10] < SNAPSHOT_DATE:
        return "ended"
    if start and f"{start}-01-01"[:10] > SNAPSHOT_DATE:
        return "not_started"
    return "running"


def within_grant(published: str | None, end: str | None) -> bool:
    return not published or not end or int(published[:4]) <= int(end[:4]) + 1


def merged_bases(links: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    bases: dict[str, set[str]] = defaultdict(set)
    for target, basis in links:
        bases[target].add(basis)
    return tuple((target, ", ".join(sorted(found))) for target, found in sorted(bases.items()))


def node_in(text: str) -> str | None:
    if found := resolve_node(text) or resolve_code_prefix(text.split("/")[-1].strip()):
        return found
    for part in re.findall(r"\(([^)]+)\)", text):
        if found := resolve_node(part) or CODES.get(part.strip().upper()) or resolve_code_prefix(part.strip()):
            return found
    return None


def role_kind(value: RoleStatementRow, evidence: str | None, crowded: bool) -> str:
    hub = any(node_in(text) == "node:hub" for text in (value.node, value.affiliation, value.person_name) if text)
    if hub and value.role_kind in LEADS and not HEADING_ROLE.search(evidence or ""):
        return "liaison"
    if crowded and value.role_kind == "task_lead":
        return "participant"
    return value.role_kind


def plan_people(written: str) -> list[str]:
    inside = re.findall(r"\(([^)]*)\)", written)
    outside = re.sub(r"\([^)]*\)", " ", PARTNER_PREFIX.sub("", written))
    parts = [name.strip(" .") for part in [outside, *inside] for name in re.split(r",|;|/|&|\band\b", part)]
    return list(dict.fromkeys(name for name in parts if is_person_name(name)))


def lead_node(value: RoleStatementRow) -> tuple[str, str] | None:
    for written in (value.node, value.affiliation):
        node_id = node_in(written) if written else None
        if written and node_id and node_id != "node:hub":
            return node_id, written
    return None


def tool_patterns(name: str, description: str | None) -> list[re.Pattern[str]]:
    patterns = [re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])")] if len(name) >= 3 else []
    head = (description or "").split(":", 1)[0] if ":" in (description or "")[:80] else ""
    initials = "".join(word[0] for word in head.split() if word[:1].isupper())
    bracketed = re.search(rf"([A-Z][\w-]*(?:\s+[\w-]+){{1,6}})\s+\({re.escape(name)}\)", description or "")
    for long in (head if len(head.split()) >= 2 and initials.upper() == name.upper() else "", bracketed[1] if bracketed else ""):
        if long:
            patterns.append(re.compile(rf"\b{re.escape(long)}\b", re.I))
    return patterns


def work_package(code: str | None) -> str | None:
    found = WORK_PACKAGE_NUMBER.match(code or "")
    return found.group(1) if found else None


def work_codes(work_item: str | None) -> list[str]:
    return [found for found in (code_key(part) for part in WORK_ITEM_CODE.findall(work_item or "")) if found]


def funding(value: RoleStatementRow, evidence: str | None) -> str:
    if value.funding != "not_stated" and not FUNDING_WORDS.search(evidence or ""):
        return "not_stated"
    return value.funding


def node_page_role(row: SourceRecord[NodePageRoleRow]) -> SourceRecord[RoleStatementRow]:
    value = row.value
    statement = RoleStatementRow(
        id=f"node_page:{value.id}",
        document=value.document,
        person_name=value.person_name,
        role=value.role,
        role_kind=value.role_kind,
        place=value.place,
        place_kind=value.place_kind,
        affiliation=value.affiliation,
        node=value.node,
        funding="not_stated",
        email=None,
    )
    return SourceRecord(statement, row.evidence)


def corrected_role(row: SourceRecord[Correction], person: str, place: str) -> SourceRecord[RoleStatementRow]:
    value = row.value
    statement = RoleStatementRow(
        id=f"correction:{row.evidence[0].location}",
        document=row.evidence[0].artifact,
        person_name=person,
        role=value.role or value.value or "member",
        role_kind=value.value or "member",
        place=place,
        place_kind="group",
        funding="not_stated",
        email=None,
    )
    return SourceRecord(statement, row.evidence)


def correction_note(value: Correction) -> str:
    return f"Confirmed by {value.confirmed_by or 'a reviewer'}{' (' + value.date + ')' if value.date else ''}: {value.note or ''}".strip()


def meaningful(name: str) -> bool:
    if plain(name) in INFRASTRUCTURE_NAMES:
        return True
    words = [word for word in plain(name).split() if word not in ("work", "package", "task", "wp", "the", "elixir")]
    return any(len(word) >= 3 and not word.isdigit() for word in words)


def owner_name(owner: str) -> str:
    if plain(owner) in INFRASTRUCTURE_NAMES:
        return "ELIXIR"
    node_id = resolve_node(owner)
    return f"{BY_ID[node_id].name} Node programme" if node_id and owner_kind(owner) == "node_programme" else owner


def owner_kind(owner: str) -> str:
    if plain(owner) in INFRASTRUCTURE_NAMES:
        return "infrastructure"
    if resolve_node(owner):
        return "node_programme"
    return guess_kind(owner, "project")


def read_documents(context: RunContext) -> Documents:
    info: dict[str, SourceRecord[DocumentInfo]] = {}
    redirects: dict[str, str] = {}
    for row in load_index(context):
        value = row.value
        if value.status == "saved" and value.path:
            info[value.path] = SourceRecord(
                DocumentInfo(
                    document_id=f"document:{slug(value.path.removeprefix('data/input/'))}",
                    path=value.path,
                    url=value.final_url or value.url,
                    retrieved_at=value.retrieved_at,
                    source=value.source,
                    content_type=value.content_type,
                ),
                row.evidence,
            )
        start, end = url_key(value.url), url_key(value.final_url)
        if start and end and start != end:
            redirects[start] = end
    return Documents(info, redirects)


class Placement:
    def __init__(
        self, initiatives: Initiatives, statements: list[SourceRecord[InitiativeStatementRow]], node_sites: set[str]
    ) -> None:
        self.initiatives = initiatives
        self.node_sites = node_sites
        self.described: dict[str, list[str]] = defaultdict(list)
        self.claimed: dict[str, set[str]] = defaultdict(set)
        for row in statements:
            initiative_id = initiatives.by_claim[f"statement:{row.value.id}"]
            self.claimed[row.value.document].add(initiative_id)
            if row.value.coverage == "described" and initiative_id not in self.described[row.value.document]:
                self.described[row.value.document].append(initiative_id)

    def family(self, initiative_id: str) -> str:
        return self.initiatives.identities[initiative_id].family

    def owner(self, document: str, name: str, prefer_project: bool, kind: str | None = None) -> str | None:
        found = self.initiatives.resolve(name, kind)
        local = self.described.get(document, [])
        projects = [i for i in local if self.family(i) == "project"]
        named = self.named_project(name)
        if prefer_project and named:
            return named
        if prefer_project and projects:
            return found if found in projects else projects[0]
        if found and found in local:
            return found
        if found is None and (subject := self.subject(document, name)):
            return subject
        if len(local) == 1 and (found is None or found not in self.claimed.get(document, set())):
            return local[0]
        return found or (local[0] if local else None)

    def named_project(self, name: str) -> str | None:
        for token in ACRONYM_TOKEN.findall(name):
            if sum(char.isupper() for char in token) >= 2 and plain(token) != "elixir":
                if (key := acronym_key(token)) and (found := self.initiatives.by_acronym.get(key)):
                    return found
        return None

    def subject(self, document: str, name: str) -> str | None:
        words = set(plain(name).split()) - {"elixir", "the", "project", "programme"}
        for initiative_id in self.described.get(document, []):
            aliases = self.initiatives.identities[initiative_id].aliases
            if words and any(words <= set(plain(alias).split()) for alias in aliases):
                return initiative_id
        return None

    def place(self, value: RoleStatementRow) -> tuple[str | None, str | None]:
        if value.place_kind in ("work_package", "task"):
            return self.named_project(value.work_item or "") or self.owner(value.document, value.place, True), value.work_item
        found = self.initiatives.resolve(value.place, guess_kind(value.place, value.place_kind))
        generic = bool(GENERIC_BODY.search(value.place))
        body = value.place_kind == "governance_body" or (value.place_kind == "group" and found is None) or generic
        if body and "elixir" not in plain(value.place):
            projects = [i for i in self.described.get(value.document, []) if self.family(i) == "project"]
            if projects:
                return projects[0], value.work_item or value.place
            if generic and value.document in self.node_sites:
                return None, value.work_item
        subject = self.subject(value.document, value.place)
        if subject and (found is None or found not in self.claimed.get(value.document, set())):
            return subject, value.work_item
        return found, value.work_item


def initiative_claims(statements: list[SourceRecord[InitiativeStatementRow]], documents: Documents) -> list[Claim]:
    claims: list[Claim] = []
    for row in statements:
        value = row.value
        base = documents.url(value.document)
        claims.append(
            Claim(
                claim_id=f"statement:{value.id}",
                name=value.name,
                acronym=value.acronym,
                kind=MERGED_KINDS.get(value.kind, value.kind),
                coverage=value.coverage,
                url=base,
                links=tuple(absolute(base, link) for link in value.links),
            )
        )
    return claims


def run(context: RunContext) -> None:
    documents = read_documents(context)
    collected = Collected()
    derived = Derived()
    biotools = list(load_biotools(context))
    events = list(load_events(context))
    materials = list(load_materials(context))
    facets = list(load_facets(context))
    zenodo = list(load_zenodo(context))
    f1000 = list(load_f1000(context))
    reviews_rows = list(load_reviews(context))
    perun = [*load_perun(context), *load_perun_2(context)]
    statements = list(load_statements(context))
    projects = list(load_projects(context))
    participants = list(load_participants(context))
    node_roles = list(load_node_roles(context))
    roles = [*load_roles(context), *(node_page_role(row) for row in node_roles)]
    corrections = list(load_corrections(context))
    plans = list(load_plan_items(context))
    directory = list(load_directory(context))
    pages = list(load_pages(context))
    candidates = list(load_candidates(context))
    elixir_events = list(load_elixir_events(context))
    recommendations = list(load_recommendations(context))
    plan_links = list(load_plan_links(context))
    domains = list(load_domains(context))
    statements = latest(context, documents, statements)
    roles = latest(context, documents, roles)
    plans = latest(context, documents, plans)
    directory = latest(context, documents, directory)
    pages = latest(context, documents, pages)
    candidates = latest(context, documents, candidates)
    elixir_events = latest(context, documents, elixir_events)
    recommendations = latest(context, documents, recommendations)
    plan_links = latest(context, documents, plan_links)
    roles = kept(context, roles, {row.value.document for row in candidates}, "superseded_by_page_parser")
    for row in pages:
        if info := documents.info.get(row.value.document):
            dated = replace(info.value, published=row.value.published, modified=row.value.modified)
            documents.info[row.value.document] = SourceRecord(dated, info.evidence + row.evidence)
    entries: dict[str, tuple[Entry, tuple[Evidence, ...]]] = {}
    for row in directory:
        value = row.value
        entry = Entry(
            claim_id=entry_id(value.name, value.kind),
            name=full_name(value.name, value.kind),
            kind=value.kind,
            status=value.status,
            url=value.url,
            start=value.start,
            end=value.end,
            became=value.became,
            became_date=value.became_date,
            document=value.document,
        )
        if entry.claim_id in entries:
            context.exclude("duplicate_record", row.evidence)
        else:
            entries[entry.claim_id] = (entry, row.evidence)
    decisions = Decisions({row.value.review_id: row for row in load_decisions(context)})

    topics: dict[str, SourceRecord[TopicEntry]] = {}
    topic_by_label: dict[str, str] = {}

    def add_topics(labels: list[str], uris: list[str], evidence: tuple[Evidence, ...]) -> list[str]:
        found: list[str] = []
        for label, uri in zip(labels, uris, strict=False):
            if not uri.startswith("http://edamontology.org/topic_"):
                continue
            topic_id = f"topic:{uri.rsplit('/', 1)[-1]}"
            if topic_id not in topics:
                topics[topic_id] = SourceRecord(TopicEntry(topic_id, label, uri), evidence)
                topic_by_label.setdefault(label.lower(), topic_id)
            found.append(topic_id)
        return list(dict.fromkeys(found))

    tool_topics = {row.value.biotools_id: add_topics(row.value.topic_labels, row.value.edam_topic_uris, row.evidence) for row in biotools}
    event_topics = {row.value.tess_id: add_topics(row.value.topic_labels, row.value.edam_topic_uris, row.evidence) for row in events}
    material_topics = {row.value.tess_id: add_topics(row.value.topic_labels, row.value.edam_topic_uris, row.evidence) for row in materials}

    def topic_ids(labels: list[str]) -> tuple[str, ...]:
        found = [topic_by_label[label.lower()] for label in labels if label.lower() in topic_by_label]
        collected.counts["topic_labels_unmatched"] += len(labels) - len(found)
        return tuple(dict.fromkeys(found))

    registry = registry_claims([entry for entry, _ in entries.values()], lambda url: page_url_key(url, documents.redirects))
    claims = [*registry, *initiative_claims(statements, documents)]
    for row in projects:
        value = row.value
        claims.append(
            Claim(
                claim_id=f"cordis:{value.grant_id}",
                name=value.title or value.acronym,
                acronym=value.acronym,
                kind="eu_project",
                coverage="described",
                url=documents.url(value.document),
                links=(),
            )
        )
    first = resolve_initiatives(claims, documents.redirects, [])
    node_sites = {path for path, info in documents.info.items() if (info.value.source or "").startswith("node-")}
    first_placement = Placement(first, statements, node_sites)
    role_claims: list[Claim] = []
    for row in roles:
        value = row.value
        if (
            value.place_kind in ("group", "project", "governance_body")
            and meaningful(value.place)
            and first_placement.place(value)[0] is None
        ):
            kind = guess_kind(value.place, value.place_kind)
            source = documents.info[value.document].value.source if value.document in documents.info else None
            name = value.place
            node_id = resolve_node((source or "").removeprefix("node-"))
            if kind in ("working_group", "governance_group") and node_id:
                kind = "node_group"
                label = BY_ID[node_id].name
                name = name if plain(label) in plain(name) else f"{name} ({label})"
            role_claims.append(
                Claim(
                    claim_id=f"role:{value.id}",
                    name=name,
                    acronym=None,
                    kind=kind,
                    coverage="listed",
                    url=None,
                    links=(),
                )
            )
    plan_claims = [
        Claim(f"plan:{row.value.id}", owner_name(row.value.owner), None, owner_kind(row.value.owner), "listed", None, ())
        for row in plans
        if meaningful(row.value.owner)
        and first_placement.owner(row.value.document, row.value.owner, row.value.kind in PLAN_PROJECT_KINDS) is None
    ]
    all_claims = [*claims, *role_claims, *plan_claims]
    initiatives = resolve_initiatives(all_claims, documents.redirects, [])
    if decided := decisions.same("initiative_match", initiatives.candidates):
        first_claim = {i: identity.claims[0] for i, identity in initiatives.identities.items()}
        initiatives = resolve_initiatives(
            all_claims, documents.redirects, [(first_claim[a], first_claim[b]) for a, b in decided]
        )
    placement = Placement(initiatives, statements, node_sites)
    claim_documents = {
        **{f"statement:{row.value.id}": row.value.document for row in statements},
        **{f"role:{row.value.id}": row.value.document for row in roles},
        **{f"plan:{row.value.id}": row.value.document for row in plans},
    }
    registry_of: dict[str, Entry] = {}
    for entry, evidence in sorted(entries.values(), key=lambda pair: priority(pair[0])):
        registry_of.setdefault(initiatives.by_claim[entry.claim_id], entry)
        collected.cite(initiatives.by_claim[entry.claim_id], evidence)

    def regrouped(identity: InitiativeIdentity) -> InitiativeIdentity:
        if entry := registry_of.get(identity.initiative_id):
            return replace(identity, kind=entry.kind, family=family(entry.kind))
        if identity.family == "project" and any(AREA_PAGE.search(page) for page in identity.pages):
            return replace(identity, kind="programme_area")
        listed = (documents.url(claim_documents[claim]) or "" for claim in identity.claims if claim in claim_documents)
        if identity.family == "project" and (
            any(claim.startswith("cordis:") for claim in identity.claims) or any(EU_PROJECT_LISTING in url for url in listed)
        ):
            return replace(identity, kind="eu_project")
        if identity.kind not in REGISTRY_KINDS:
            return identity
        places = [claim_documents[claim] for claim in identity.claims if claim in claim_documents]
        kind = "node_group" if places and all(place in node_sites for place in places) else "other_group"
        return replace(identity, kind=kind, family=family(kind))

    initiatives.identities = {key: regrouped(identity) for key, identity in initiatives.identities.items()}
    phrases = Phrases([entry for entry, _ in entries.values()], initiatives.by_claim)
    primary_key = {key: url_key(identity.pages[0]) for key, identity in initiatives.identities.items() if identity.pages}
    page_rows = {
        key: row for row in pages if (key := page_url_key(documents.url(row.value.document), documents.redirects))
    }

    for row in statements:
        collected.cite(initiatives.by_claim[f"statement:{row.value.id}"], row.evidence)
    for row in projects:
        collected.cite(initiatives.by_claim[f"cordis:{row.value.grant_id}"], row.evidence)
    role_initiative: dict[str, tuple[str | None, str | None]] = {}
    for row in roles:
        value = row.value
        if value.place_kind in ("node", "hub", "organisation"):
            continue
        claim = initiatives.by_claim.get(f"role:{value.id}")
        role_initiative[value.id] = (claim, value.work_item) if claim else placement.place(value)
        if claim:
            collected.cite(claim, row.evidence)

    stated: dict[str, list[Stated]] = defaultdict(list)
    funded: dict[str, Funded] = {}
    statement_links: list[tuple[SourceRecord[InitiativeStatementRow], SourceRecord[StatementLink]]] = []
    node_sets: dict[str, dict[frozenset[str], list[str | None]]] = defaultdict(lambda: defaultdict(list))
    linked_outputs: dict[str, set[tuple[str, str]]] = defaultdict(set)
    activity: dict[str, set[tuple[str, str, str, str]]] = defaultdict(set)
    for row in statements:
        value = row.value
        initiative_id = initiatives.by_claim[f"statement:{value.id}"]
        identity = initiatives.identities[initiative_id]
        url = documents.url(value.document)
        located = documents.located(value.document)
        own = url_key(url)
        own = documents.redirects.get(own, own) if own else None
        primary = bool(identity.pages) and own is not None and f"https://{own}" == identity.pages[0]
        stated[initiative_id].append(
            Stated(
                url=url,
                coverage=value.coverage,
                primary=primary,
                start=value.start,
                end=value.end,
                status=value.status,
                summary=value.summary,
                outcomes=tuple(value.outcomes),
                contacts=tuple(value.contacts),
            )
        )
        statement_links.append(
            (
                row,
                SourceRecord(
                    StatementLink(
                        statement_id=f"statement:{digest(value.id)}",
                        initiative_id=initiative_id,
                        evidence=quote(row),
                        located=located,
                        topics=topic_ids(value.topics) if value.coverage == "described" else (),
                    ),
                    row.evidence,
                ),
            )
        )
        stated_nodes: set[str] = set()
        for name in value.nodes:
            node_id = resolve_node(name)
            if node_id is None:
                collected.counts["statement_nodes_unresolved"] += 1
                continue
            stated_nodes.add(node_id)
            link = EdgeLink(node_id, initiative_id, name, located, None, "own_page" if primary else "stated")
            collected.edge("takes_part_in", link, row.evidence)
        if len(stated_nodes) >= 2:
            node_sets[initiative_id][frozenset(stated_nodes)].append(url)
        for name in value.related:
            related = initiatives.resolve(name)
            if related is None:
                collected.counts["statement_related_unresolved"] += 1
            elif related != initiative_id:
                said = quote(row) if name.lower() in (quote(row) or "").lower() else None
                collected.edge("related_to", EdgeLink(initiative_id, related, name, located, quote=said), row.evidence)
                published = documents.info[value.document].value.published if value.document in documents.info else None
                if identity.family == "project" and published and value.coverage == "described":
                    activity[related].add((published, "listed on a project page (indirect)", identity.name, url or ""))
                collected.edge("related_to", EdgeLink(related, initiative_id, identity.name, located, None, "reverse", said), row.evidence)
        for link in value.links:
            key = url_key(absolute(url, link))
            if key:
                linked_outputs[key].add((initiative_id, "linked"))
            if record_id := zenodo_record_id(link):
                linked_outputs[f"zenodo:{record_id}"].add((initiative_id, "linked"))
    for row in projects:
        value = row.value
        initiative_id = initiatives.by_claim[f"cordis:{value.grant_id}"]
        funded[initiative_id] = Funded(
            url=documents.url(value.document),
            grant_id=value.grant_id,
            start=value.start,
            end=value.end,
            objective=value.objective,
            total_cost_eur=value.total_cost_eur,
            eu_contribution_eur=value.eu_contribution_eur,
        )
        documents.located(value.document)
    for initiative_id, sets in node_sets.items():
        if len(sets) > 1:
            name = initiatives.identities[initiative_id].name
            collected.add_review(
                review(
                    "value_conflict",
                    f"Sources list different Nodes for {name}. Which Nodes take part?",
                    [initiative_id],
                    [name],
                    [option(", ".join(sorted(BY_ID[n].name for n in nodes)), urls) for nodes, urls in sets.items()],
                    "nodes",
                )
            )

    def finished(identity: InitiativeIdentity, record: InitiativeRecord) -> InitiativeRecord:
        entry = registry_of.get(identity.initiative_id)
        page = page_rows.get(primary_key.get(identity.initiative_id) or "")
        status = record.status if record.status != "planned" or (record.start or "") > SNAPSHOT_MONTH else None
        if page:
            collected.cite(identity.initiative_id, page.evidence)
            documents.located(page.value.document)
            url = documents.url(page.value.document)
            for shown, target in zip(page.value.contacts, page.value.contact_targets, strict=False):
                if shown.lower() != target.lower():
                    collected.add_review(
                        review(
                            "value_conflict",
                            f"The contact link on the page of {identity.name} shows {shown} but sends to {target}. Which address is right?",
                            [identity.initiative_id],
                            [identity.name],
                            [option(shown, [url]), option(target, [url])],
                            "contact",
                        )
                    )
        scientific = identity.family == "project" and any(SCIENTIFIC_PROGRAMME in page_url for page_url in identity.pages)
        return replace(
            record,
            status=entry.status if entry else status,
            start=record.start or (entry.start if entry else None),
            end=record.end or (entry.end if entry else None),
            contacts=tuple(page.value.contacts) if page and page.value.contacts else record.contacts,
            join_url=page.value.join_url if page else None,
            joining=page.value.joining if page else None,
            programme=PROGRAMME if scientific else None,
            period_status=None if entry else period_status(record.start, record.end),
        )

    initiative_records: dict[str, InitiativeRecord] = {}
    for identity in initiatives.identities.values():
        record, conflicts = merge_initiative(
            identity, stated.get(identity.initiative_id, []), funded.get(identity.initiative_id), decisions
        )
        for conflict in conflicts:
            collected.add_review(conflict)
        initiative_records[identity.initiative_id] = finished(identity, record)
    for row in corrections:
        value = row.value
        if value.property != "kind":
            continue
        if value.subject not in initiative_records or not value.value:
            context.exclude("correction_target_missing", row.evidence)
            continue
        identity = initiatives.identities[value.subject]
        initiatives.identities[value.subject] = replace(identity, kind=value.value, family=family(value.value))
        initiative_records[value.subject] = replace(initiative_records[value.subject], kind=value.value)
        collected.cite(value.subject, row.evidence)
        collected.counts["corrections_applied"] += 1

    for entry, evidence in entries.values():
        source = initiatives.by_claim[entry.claim_id]
        target = (phrases.one(entry.became) or initiatives.resolve(entry.became)) if entry.became else None
        collected.counts["became_targets_unresolved"] += bool(entry.became) and target is None
        collected.counts["became_same_initiative"] += target == source
        if target and target != source:
            located = documents.located(entry.document)
            link = BecameLink(source, target, entry.became_date, f"{entry.name} became the {entry.became}", located)
            context.map(BECAME, SourceRecord(link, evidence))

    sub_projects: dict[tuple[str, str], str] = {}
    for row in plans:
        number = work_package(row.value.code)
        titled = ":" in row.value.label
        head = row.value.label.split(":", 1)[0] if titled else row.value.label
        found = (titled and placement.named_project(head)) or initiatives.resolve(head, "commissioned_service")
        if row.value.kind == "work_package" and number and found and placement.family(found) == "project":
            sub_projects[(row.value.document, number)] = found
            for area in placement.described.get(row.value.document, []):
                if area != found and initiatives.identities[area].kind == "programme_area":
                    link = EdgeLink(found, area, initiatives.identities[area].name, documents.located(row.value.document), None, "work_plan")
                    collected.edge("part_of", link, row.evidence)
    page_owner = {url_key(page): key for key, identity in initiatives.identities.items() for page in identity.pages}
    for key, identity in initiatives.identities.items():
        for page in identity.pages:
            own = url_key(page) or ""
            parents = [parent for parent in page_owner if parent and own.startswith(f"{parent}/") and page_owner[parent] != key]
            if parents:
                parent = page_owner[max(parents, key=len)]
                link = EdgeLink(key, parent, initiatives.identities[parent].name, Located(None, page, None), None, "sub_page")
                collected.edge("part_of", link, collected.cited(key, limit=3))

    planned: dict[tuple[str, str], list[PlannedItem]] = defaultdict(list)
    plan_rows: dict[tuple[str, str], list[SourceRecord[PlanItemRow]]] = defaultdict(list)
    document_starts = {
        document: min(starts)
        for document, ids in placement.described.items()
        if (starts := [start for i in ids if placement.family(i) == "project" and (start := initiative_records[i].start) and "-" in start])
    }
    for row in plans:
        value = row.value
        prefer = value.kind in PLAN_PROJECT_KINDS
        initiative_id = (
            sub_projects.get((value.document, work_package(value.code) or ""))
            or initiatives.by_claim.get(f"plan:{value.id}")
            or placement.owner(value.document, value.owner, prefer)
        )
        if initiative_id is None:
            context.exclude("plan_owner_unresolved", row.evidence)
            continue
        crowded = len([name for written in value.leads for name in plan_people(written)]) > MAX_WORK_LEADS
        collected.counts["crowded_plan_lead_lists"] += crowded
        item = PlannedItem(
            initiative_id=initiative_id,
            initiative_name=initiatives.identities[initiative_id].name,
            kind=value.kind,
            code=value.code,
            label=value.label,
            description=value.description,
            parent=value.parent,
            date=value.date,
            date_as_written=value.date_as_written,
            status=value.status,
            leads=() if crowded else tuple(value.leads),
            participants=(*value.leads, *value.participants) if crowded else tuple(value.participants),
            effort=value.effort,
            link=value.link,
            url=documents.url(value.document),
            evidence=quote(row),
            topics=topic_ids(value.topics),
            month_start=document_starts.get(value.document),
        )
        planned[plan_key(item)].append(item)
        if f"plan:{value.id}" in initiatives.by_claim:
            collected.cite(initiative_id, row.evidence)
            if node_id := resolve_node(value.owner):
                link = EdgeLink(node_id, initiative_id, value.owner, documents.located(value.document))
                collected.edge("takes_part_in", link, row.evidence)
        plan_rows[plan_key(item)].append(row)
    plan_records: list[SourceRecord[PlanItemRecord]] = []
    plan_by_code: dict[tuple[str, str], str] = {}
    plain_codes: dict[tuple[str, str], set[str]] = defaultdict(set)
    plan_of_row: dict[str, str] = {}
    outputs_of_plan: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for key in sorted(planned):
        record, conflicts, set_aside = merge_plan_items(planned[key], decisions, initiative_records[key[0]].start)
        collected.counts["plan_mentions_set_aside"] += set_aside
        evidence = tuple(e for row in plan_rows[key] for e in row.evidence)
        plan_records.append(SourceRecord(record, evidence))
        collected.cite(record.plan_item_id, evidence)
        for conflict in conflicts:
            collected.add_review(conflict)
        if code := scoped_code(record.code, record.parent):
            plan_by_code.setdefault((record.initiative_id, code), record.plan_item_id)
        if code := code_key(record.code):
            plain_codes[(record.initiative_id, code)].add(record.plan_item_id)
        for row in plan_rows[key]:
            plan_of_row[row.value.id] = record.plan_item_id
        if record.link and (record_id := zenodo_record_id(record.link)):
            outputs_of_plan[f"zenodo:{record_id}"].add((record.plan_item_id, record.initiative_id))

    for key, ids in plain_codes.items():
        if len(ids) == 1:
            plan_by_code.setdefault(key, next(iter(ids)))
    deliverables: dict[str, list[tuple[str, str, set[str]]]] = defaultdict(list)
    plan_words = {plan.value.plan_item_id: label_words(plan.value.label) for plan in plan_records}
    for plan in plan_records:
        if plan.value.kind in ("deliverable", "milestone") and (code := code_key(plan.value.code)):
            deliverables[code].append((plan.value.plan_item_id, plan.value.initiative_id, label_words(plan.value.label)))

    mentions: list[Mention] = []
    mention_evidence: dict[str, tuple[Evidence, ...]] = {}

    def mention(key: str, name: str, kind: str, evidence: tuple[Evidence, ...], **extra: str | None) -> str:
        mentions.append(Mention(key=key, name=name, source_kind=kind, **extra))
        mention_evidence[key] = evidence
        return key

    for row in perun:
        value = row.value
        if not is_person_name(value.person_name):
            context.exclude("perun_account_not_a_person", row.evidence)
            continue
        mention(
            f"perun:{row.evidence[0].artifact}:{row.evidence[0].location}",
            value.person_name,
            "perun",
            row.evidence,
            email=email_of(value.email),
            perun_account=value.lifescienceid_username or value.logins,
            perun_organisation=value.organization,
        )
    node_orcids = {f"node_page:{row.value.id}": orcid_of(row.value.orcid) for row in node_roles if row.value.orcid}
    for row in roles:
        value = row.value
        if is_person_name(value.person_name):
            mention(
                f"role:{value.id}", value.person_name, "role_statement", row.evidence, email=email_of(value.email), orcid=node_orcids.get(value.id)
            )
    plan_people_links: list[tuple[str, str, SourceRecord[PlanItemRow], str]] = []
    group_names = {group_key(alias) for identity in initiatives.identities.values() for alias in (identity.name, *identity.aliases)}

    def plan_persons(written: str) -> list[str]:
        found = [name for name in plan_people(written) if group_key(name) not in group_names and not resolve_node(name)]
        collected.counts["plan_people_named_like_groups"] += len(plan_people(written)) - len(found)
        return found

    for row in plans:
        if row.value.id not in plan_of_row:
            continue
        leads = [(written, name) for written in row.value.leads for name in plan_persons(written)]
        crowded = len(leads) > MAX_WORK_LEADS
        collected.counts["crowded_plan_leads_as_participants"] += len(leads) if crowded else 0
        listed = [
            *((written, name, "participant" if crowded else "lead") for written, name in leads),
            *((written, name, "participant") for written in row.value.participants for name in plan_persons(written)),
        ]
        for index, (written, name, role) in enumerate(listed):
            key = mention(f"plan:{row.value.id}:{index}", name, "plan_item", row.evidence)
            plan_people_links.append((key, written, row, role))
    for row in candidates:
        mention(f"candidate:{row.value.id}", row.value.person, "election_candidate", row.evidence)
    known_names = {name_key(m.name) for m in mentions if m.source_kind in ("role_statement", "plan_item", "election_candidate")}

    tool_names: dict[str, set[str]] = defaultdict(set)
    tool_pages: dict[str, set[str]] = defaultdict(set)
    for row in biotools:
        for written in (row.value.name, row.value.biotools_id):
            if written:
                tool_names[plain(written)].add(row.value.biotools_id)
        if page := url_key(row.value.homepage):
            tool_pages[page].add(row.value.biotools_id)
        tool_pages[f"bio.tools/{row.value.biotools_id.lower()}"].add(row.value.biotools_id)
    recommended: dict[str, list[SourceRecord[RecommendationRow]]] = defaultdict(list)
    recommendation_links: list[tuple[SourceRecord[RecommendationRow], SourceRecord[RecommendationLink]]] = []
    for row in recommendations:
        initiative_id = phrases.one(row.value.group)
        if initiative_id is None:
            context.exclude("recommendation_group_unresolved", row.evidence)
            continue
        resource_id = f"resource:{slug(plain(row.value.resource))}"
        recommended[resource_id].append(row)
        located = documents.located(row.value.document)
        link = RecommendationLink(initiative_id, resource_id, located, quote(row))
        recommendation_links.append((row, SourceRecord(link, row.evidence)))
    resource_tools: set[str] = set()
    resource_tool_ids: dict[str, list[str]] = {}
    for resource_id, rows in sorted(recommended.items()):
        names = Counter(r.value.resource for r in rows)
        kinds = Counter(r.value.kind for r in rows)
        name = sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        kind = sorted(kinds.items(), key=lambda item: (-item[1], item[0]))[0][0]
        by_url = {tool for r in rows if (page := url_key(r.value.url)) for tool in tool_pages.get(page, set())}
        by_name = tool_names.get(plain(name), set())
        matched: list[tuple[str, str]] = []
        if len(by_url) == 1:
            matched = [(next(iter(by_url)), "url")]
        elif kind in TOOL_RESOURCES and len(by_name) == 1:
            matched = [(next(iter(by_name)), "name")]
        resource_tools.update(tool for tool, _ in matched)
        resource_tool_ids[resource_id] = [tool for tool, _ in matched]
        record = ResourceRecord(
            resource_id, name, kind, next((r.value.url for r in rows if r.value.url), None), tuple((f"tool:{tool}", basis) for tool, basis in matched)
        )
        context.map(RESOURCES, SourceRecord(record, tuple(e for r in rows for e in r.evidence)))
    tool_recommenders: dict[str, set[tuple[str, str]]] = defaultdict(set)
    group_resources: dict[str, list[str]] = defaultdict(list)
    for row, link in recommendation_links:
        basis = "develops" if row.value.basis == "develops" else "recommends"
        group_resources[link.value.initiative_id].append(row.value.resource)
        derived.share("resource", link.value.resource_id, row.value.resource, link.value.initiative_id, link.value.located.url, row.evidence)
        for tool in resource_tool_ids.get(link.value.resource_id, []):
            tool_recommenders[tool].add((link.value.initiative_id, basis))
    domain_tools: dict[str, list[SourceRecord[BiotoolsDomain]]] = defaultdict(list)
    for row in domains:
        domain_tools[row.value.biotools_id].append(row)

    def admitted(row: SourceRecord[BiotoolsTool]) -> bool:
        value = row.value
        tagged = bool(value.elixir_nodes or value.elixir_platforms or value.elixir_communities)
        listed = value.biotools_id in domain_tools or value.biotools_id in resource_tools
        return tagged or listed or any(name_key(name) in known_names for name in value.person_names)

    tool_admitted: list[SourceRecord[BiotoolsTool]] = []
    for row in biotools:
        if admitted(row):
            tool_admitted.append(row)
        else:
            context.exclude("biotools_without_elixir_tag", row.evidence)
    tool_people: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in tool_admitted:
        value = row.value
        for index, name in enumerate(value.person_names):
            kind = value.credit_types[index] if index < len(value.credit_types) else ""
            if kind in ("", "Person") and is_person_name(name):
                orcid = orcid_of(value.orcids[index]) if index < len(value.orcids) else None
                email = email_of(value.credit_emails[index]) if index < len(value.credit_emails) else None
                key = mention(f"biotools:{value.biotools_id}:{index}", name, "biotools", row.evidence, orcid=orcid, email=email)
                tool_people[value.biotools_id].append((key, name))
            else:
                collected.counts["tool_credits_not_people"] += 1
    output_authors: dict[str, list[tuple[str, int, str, str]]] = defaultdict(list)
    for row in zenodo:
        value = row.value
        credited = [
            *((name, at(value.orcids, index), at(value.creator_affiliations, index)) for index, name in enumerate(value.person_names)),
            *(
                (name, at(value.contributor_orcids, index), at(value.contributor_affiliations, index))
                for index, name in enumerate(value.contributor_names)
            ),
        ]
        for index, (name, written_orcid, affiliation) in enumerate(credited):
            orcid = orcid_of(written_orcid)
            if is_person_name(name) or orcid:
                key = mention(f"zenodo:{value.record_id}:{index}", name, "zenodo", row.evidence, orcid=orcid)
                output_authors[f"zenodo:{value.record_id}"].append((key, index + 1, name, affiliation))
            else:
                collected.counts["output_authors_not_people"] += 1
    for row in f1000:
        value = row.value
        output_id = f"f1000:{slug(value.item_path)}"
        for index, name in enumerate(value.person_names):
            if is_person_name(name):
                key = mention(f"f1000:{value.item_path}:{index}", name, "f1000", row.evidence)
                output_authors[output_id].append((key, index + 1, name, ""))
            else:
                collected.counts["output_authors_not_people"] += 1
    people = resolve_people(mentions, [])
    if decided_people := decisions.same("person_match", people.candidates):
        first_mention = {i: identity.mentions[0] for i, identity in people.identities.items()}
        people = resolve_people(mentions, [(first_mention[a], first_mention[b]) for a, b in decided_people])

    partners = [(row.value.organisation, row.value.country, row.value.activity_type) for row in participants]
    affiliations = [
        *(value.affiliation for row in roles if (value := row.value).affiliation and is_person_name(value.person_name)),
        *(row.value.place for row in roles if row.value.place_kind == "organisation"),
        *(row.value.affiliation for row in candidates if row.value.affiliation),
    ]
    organisations = resolve_organisations(partners, affiliations, [])
    if decided_organisations := decisions.same("organisation_match", organisations.candidates):
        organisations = resolve_organisations(partners, affiliations, decided_organisations)
    organisation_evidence: dict[str, set[Evidence]] = defaultdict(set)
    for row in roles:
        value = row.value
        for name in (value.affiliation, value.place if value.place_kind == "organisation" else None):
            if name and (organisation_id := organisations.of(name)):
                organisation_evidence[organisation_id].update(row.evidence)
    for row in candidates:
        if row.value.affiliation and (organisation_id := organisations.of(row.value.affiliation)):
            organisation_evidence[organisation_id].update(row.evidence)
    for row in participants:
        if organisation_id := organisations.of(row.value.organisation):
            organisation_evidence[organisation_id].update(row.evidence)
        initiative_id = initiatives.by_claim.get(f"cordis:{row.value.grant_id}")
        if organisation_id and initiative_id:
            located = documents.located(row.value.document)
            context.map(PARTICIPATIONS, row, SourceRecord(ParticipationLink(organisation_id, initiative_id, located), row.evidence))
            node_id = node_in(row.value.organisation) or resolve_node(row.value.country)
            if node_id and BY_ID[node_id].kind != "hub":
                written = f"{row.value.organisation} ({row.value.country})"
                contribution = f"; net EU contribution EUR {row.value.net_eu_contribution_eur:,.0f}" if row.value.net_eu_contribution_eur else ""
                derived.beneficiaries[(node_id, initiative_id)].add(f"{row.value.organisation} ({row.value.participation}{contribution})")
                collected.edge("takes_part_in", EdgeLink(node_id, initiative_id, written, located, None, "beneficiary_country"), row.evidence)
            else:
                collected.counts["beneficiaries_without_node"] += 1

    work_leads: dict[tuple[str, str | None, str], set[str]] = defaultdict(set)
    for row in roles:
        initiative_id, work_item = role_initiative.get(row.value.id, (None, None))
        on_project_page = "/eu-projects/" in (documents.url(row.value.document) or "")
        if row.value.role_kind == "task_lead" and on_project_page and (codes := work_codes(work_item)):
            work_leads[(row.value.document, initiative_id, "/".join(codes))].add(row.value.person_name)
    lead_sets: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    person_nodes: dict[str, dict[str, set[str | None]]] = defaultdict(lambda: defaultdict(set))
    removed_roles = {(row.value.subject, row.value.target) for row in corrections if row.value.property == "role" and row.value.action == "remove"}
    own_leads: set[tuple[str, str]] = set()
    for row in roles:
        value = row.value
        person_id = people.person_of(f"role:{value.id}")
        initiative_id, work_item = role_initiative.get(value.id, (None, None))
        primary = primary_key.get(initiative_id or "")
        own_page = primary is not None and page_url_key(documents.url(value.document), documents.redirects) == primary
        if person_id and initiative_id in registry_of and not work_item and value.role_kind in LEAD_CLAIMS and own_page:
            own_leads.add((person_id, initiative_id))
    led_on_own_page = {initiative_id for _, initiative_id in own_leads}
    unconfirmed: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in roles:
        value = row.value
        person_id = people.person_of(f"role:{value.id}")
        if person_id is None:
            context.exclude("role_holder_not_a_person", row.evidence)
            continue
        located = documents.located(value.document)
        url = documents.url(value.document)
        advisory = bool(ADVISORY_ROLE.search(value.role))
        placed_in_node = value.place_kind in ("node", "hub")
        for written in (value.node, value.affiliation, value.person_name):
            if written and not advisory and not placed_in_node and (node_id := node_in(written)):
                collected.edge("in_node", EdgeLink(person_id, node_id, written, located), row.evidence)
                person_nodes[person_id][node_id].add(url)
                break
        if value.affiliation and (organisation_id := organisations.of(value.affiliation)):
            collected.edge("affiliated_with", EdgeLink(person_id, organisation_id, value.affiliation, located), row.evidence)
        if value.place_kind in ("node", "hub"):
            node_id = resolve_node(value.place) or ("node:hub" if value.place_kind == "hub" else None)
            if node_id is None:
                context.exclude("role_place_unresolved", row.evidence)
                continue
            if advisory:
                collected.counts["node_advisory_roles"] += 1
                continue
            collected.edge("in_node", EdgeLink(person_id, node_id, value.place, located, value.role), row.evidence)
            person_nodes[person_id][node_id].add(url)
            continue
        if value.place_kind == "organisation":
            organisation_id = organisations.of(value.place)
            if organisation_id is None:
                context.exclude("role_place_unresolved", row.evidence)
                continue
            collected.edge("affiliated_with", EdgeLink(person_id, organisation_id, value.place, located, value.role), row.evidence)
            continue
        initiative_id, work_item = role_initiative.get(value.id, (None, None))
        if initiative_id is None:
            context.exclude("role_place_unresolved", row.evidence)
            continue
        if (person_id, initiative_id) in removed_roles:
            collected.counts["roles_removed_by_correction"] += 1
            continue
        codes = work_codes(work_item)
        crowded = bool(codes) and len(work_leads[(value.document, initiative_id, "/".join(codes))]) > MAX_WORK_LEADS
        kind = role_kind(value, quote(row), crowded)
        collected.counts["crowded_work_leads_as_participants"] += kind != value.role_kind and crowded
        if kind == "lead" and not work_item and initiatives.identities[initiative_id].kind == "community":
            kind = "co_lead"
            collected.counts["community_leads_as_co_leads"] += 1
        primary = primary_key.get(initiative_id)
        own_page = primary is not None and page_url_key(url, documents.redirects) == primary
        if kind in LEAD_CLAIMS and not work_item and initiative_id in led_on_own_page and (person_id, initiative_id) not in own_leads:
            kind = UNCONFIRMED_LEAD
            unconfirmed[(person_id, initiative_id)].add(url or value.document)
        context.map(
            HOLDS_ROLE,
            row,
            SourceRecord(
                RoleLink(person_id, initiative_id, work_item, kind, funding(value, quote(row)), quote(row), located),
                row.evidence,
            ),
        )
        derived.role(person_id, initiative_id, kind, value.role, work_item, row.evidence, url)
        if work_item and codes:
            tried = [f"{codes[0]}/{codes[-1]}", codes[-1]] if len(codes) > 1 else [codes[0]]
            plan_item_id = next((found for code in tried if (found := plan_by_code.get((initiative_id, code)))), None)
            if plan_item_id:
                role = "lead" if kind in WORK_LEADS else "participant"
                link = EdgeLink(person_id, plan_item_id, value.person_name, located, role)
                collected.edge("works_on_plan_item", link, row.evidence)
            if kind in ("work_package_lead", "task_lead"):
                lead_sets[(initiative_id, f"lead of {tried[0].upper()}")][value.document].add(person_id)
        elif not work_item and kind in LEADS and (own_page or initiative_id not in led_on_own_page):
            lead_sets[(initiative_id, "leads")][value.document].add(person_id)
        lead = lead_node(value) if initiative_id in registry_of and kind in LEAD_NODE_ROLES and not work_item else None
        if lead and page_url_key(url, documents.redirects) == primary_key.get(initiative_id):
            node_id, written = lead
            link = EdgeLink(node_id, initiative_id, f"{value.person_name} ({written})", located, None, "lead_node")
            collected.edge("takes_part_in", link, row.evidence)
    for row in corrections:
        value = row.value
        if value.property != "role" or value.action != "add":
            continue
        person_id, initiative_id = value.subject, value.target or ""
        if person_id not in people.identities or initiative_id not in initiatives.identities:
            context.exclude("correction_target_missing", row.evidence)
            continue
        kind = value.value or "member"
        statement = corrected_role(row, people.identities[person_id].name, initiatives.identities[initiative_id].name)
        link = RoleLink(person_id, initiative_id, None, kind, "not_stated", correction_note(value), CORRECTED)
        context.map(HOLDS_ROLE, statement, SourceRecord(link, row.evidence))
        derived.role(person_id, initiative_id, kind, statement.value.role, None, row.evidence, None)
        derived.involve(person_id, initiative_id, "correction", row.evidence, None)
        collected.cite(initiative_id, row.evidence)
        collected.counts["corrections_applied"] += 1
    for (person_id, initiative_id), urls in sorted(unconfirmed.items()):
        name, group = people.identities[person_id].name, initiatives.identities[initiative_id].name
        own = initiatives.identities[initiative_id].pages[0] if initiatives.identities[initiative_id].pages else None
        collected.add_review(
            review(
                "value_conflict",
                f"Another source names {name} as a lead of the {group}, but its own ELIXIR page does not. Is {name} a current lead?",
                [person_id, initiative_id],
                [name, group],
                [option("current lead", list[str | None](sorted(urls))), option("not a current lead", [own])],
                "leader",
            )
        )
    for key, written, row, role in plan_people_links:
        person_id = people.person_of(key)
        plan_item_id = plan_of_row.get(row.value.id)
        if person_id and plan_item_id:
            located = documents.located(row.value.document)
            collected.edge("works_on_plan_item", EdgeLink(person_id, plan_item_id, written, located, role), row.evidence)
            if node_id := node_in(written):
                collected.edge("in_node", EdgeLink(person_id, node_id, written, located), row.evidence)
    for row in candidates:
        value = row.value
        person_id = people.person_of(f"candidate:{value.id}")
        initiative_id = phrases.one(full_name(value.community, "community"))
        located = documents.located(value.document)
        if person_id is None:
            context.exclude("role_holder_not_a_person", row.evidence)
        elif initiative_id is None:
            context.exclude("role_place_unresolved", row.evidence)
        else:
            link = RoleLink(person_id, initiative_id, None, "candidate", "not_stated", quote(row), located)
            context.map(CANDIDATES, row, SourceRecord(link, row.evidence))
            note = f" ({value.note})" if value.note else ""
            derived.role(person_id, initiative_id, "candidate", f"2026 co-lead election candidate{note}", None, row.evidence, located.url)
            if value.country and (node_id := resolve_node(value.country)):
                collected.edge("in_node", EdgeLink(person_id, node_id, value.country, located), row.evidence)
            if value.affiliation and (organisation_id := organisations.of(value.affiliation)):
                collected.edge("affiliated_with", EdgeLink(person_id, organisation_id, value.affiliation, located), row.evidence)

    described_documents = {(initiative_id, document) for document, ids in placement.described.items() for initiative_id in ids}
    for (initiative_id, prop), per_document in lead_sets.items():
        relevant = {doc: ids for doc, ids in per_document.items() if (initiative_id, doc) in described_documents or prop != "leads"}
        distinct = {frozenset(ids) for ids in relevant.values()}
        if len(distinct) > 1:
            name = initiatives.identities[initiative_id].name
            collected.add_review(
                review(
                    "value_conflict",
                    f"Sources name different people for the {prop} of {name}. Who holds it?",
                    [initiative_id],
                    [name],
                    [
                        option(", ".join(sorted(people.identities[p].name for p in ids)), [documents.url(doc)])
                        for doc, ids in sorted(relevant.items())
                    ],
                    prop,
                )
            )
    for person_id, nodes in person_nodes.items():
        members = {node for node in nodes if BY_ID[node].kind == "member_node"}
        if len(members) > 1:
            name = people.identities[person_id].name
            collected.add_review(
                review(
                    "value_conflict",
                    f"Sources place {name} in different ELIXIR Nodes. Which is their Node?",
                    [person_id],
                    [name],
                    [option(BY_ID[node].name, list(nodes[node])) for node in sorted(members)],
                    "node",
                )
            )

    for key in sorted(planned):
        for item, row in zip(planned[key], plan_rows[key], strict=True):
            located = documents.located(row.value.document)
            for name in [*item.leads, *item.participants]:
                node_id = resolve_node(name) or resolve_code_prefix(name.split("/")[-1].strip())
                if node_id:
                    collected.edge("takes_part_in", EdgeLink(node_id, item.initiative_id, name, located), row.evidence)


    grant_initiative = {row.value.grant_id: initiatives.by_claim[f"cordis:{row.value.grant_id}"] for row in projects}
    acronym_index: dict[str, set[str]] = defaultdict(set)
    group_index: dict[str, set[str]] = defaultdict(set)
    for identity in initiatives.identities.values():
        if identity.family == "project" and (acronym := acronym_key(identity.acronym)):
            acronym_index[acronym].add(identity.initiative_id)
        if identity.kind in ("community", "platform", "focus_group"):
            for alias in identity.aliases:
                group_index[group_key(alias)].add(identity.initiative_id)

    def group_authors(names: list[str]) -> set[tuple[str, str]]:
        return {(initiative_id, "author") for name in names if not is_person_name(name) for initiative_id in phrases.find(name)}

    def named(title: str | None, keywords: list[str], description: str | None) -> set[tuple[str, str]]:
        found: set[tuple[str, str]] = set()
        for tokens, basis in ((ACRONYM_TOKEN.findall(title or ""), "title"), (keywords, "named")):
            for token in tokens:
                key = acronym_key(token) if sum(char.isupper() for char in token) >= 2 else None
                if key and len(acronym_index.get(key, set())) == 1:
                    found.add((next(iter(acronym_index[key])), basis))
        for keyword in keywords:
            key = group_key(keyword)
            qualified = GROUP_QUALIFIER.search(keyword)
            if key and qualified and len(group_index.get(key, set())) == 1:
                found.add((next(iter(group_index[key])), "named"))
        found.update((initiative_id, "title") for initiative_id in phrases.find(title))
        found.update((initiative_id, "description") for initiative_id in phrases.find(description))
        return found

    zenodo_links: dict[str, tuple[set[tuple[str, str]], set[tuple[str, str]]]] = {}
    for row in zenodo:
        value = row.value
        output_id = f"zenodo:{value.record_id}"
        links = set(linked_outputs.get(output_id, set()))
        for code in value.grant_codes:
            if code in grant_initiative and within_grant(value.publication_date, initiative_records[grant_initiative[code]].end):
                links.add((grant_initiative[code], "grant"))
            elif code in grant_initiative:
                collected.counts["grant_links_after_project_end"] += 1
        for code in [*value.grant_codes, *value.grant_acronyms]:
            for token in re.split(r"[^A-Za-z0-9]+", code) if code not in grant_initiative else []:
                key = acronym_key(token) if sum(char.isalpha() for char in token) >= 3 else None
                if key and len(named_grant := acronym_index.get(key, set())) == 1:
                    links.add((next(iter(named_grant)), "grant"))
        links |= named(value.title, value.keywords, value.description) | group_authors([*value.person_names, *value.contributor_names])
        delivered = {(plan_item_id, "link") for plan_item_id, _ in outputs_of_plan.get(output_id, set())}
        for code in DELIVERABLE_CODE.findall(value.title or ""):
            titled = label_words(value.title or "")
            for grant in value.grant_codes:
                initiative_id = grant_initiative.get(grant)
                plan_item_id = plan_by_code.get((initiative_id or "", code_key(code) or ""))
                if initiative_id and plan_item_id and (len(titled) <= 3 or plan_words[plan_item_id] & titled):
                    delivered.add((plan_item_id, "code"))
                    outputs_of_plan[output_id].add((plan_item_id, initiative_id))
            if not any(basis == "code" for _, basis in delivered):
                matches = [
                    (plan_item_id, initiative_id)
                    for plan_item_id, initiative_id, words in deliverables.get(code_key(code) or "", [])
                    if len(words & titled) >= max(2, len(words) / 2) and initiative_id in {linked for linked, _ in links}
                ]
                if len(matches) == 1:
                    delivered.add((matches[0][0], "code"))
                    outputs_of_plan[output_id].add(matches[0])
        links |= {(initiative_id, "deliverable") for _, initiative_id in outputs_of_plan.get(output_id, set())}
        zenodo_links[output_id] = (links, delivered)

    series: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in zenodo:
        if found := SERIES.match(row.value.title or ""):
            links, _ = zenodo_links[f"zenodo:{row.value.record_id}"]
            series[(plain(found[1]), code_key(found[2]) or "")] |= {
                initiative_id for initiative_id, basis in links if basis in SERIES_BASES and initiatives.identities[initiative_id].family == "project"
            }
    series_plans: dict[str, set[str]] = defaultdict(set)
    for (prefix, code), owners in series.items():
        if len(owners) == 1:
            series_plans[prefix] |= {doc for (doc, number), project in sub_projects.items() if f"wp{number}" == code and project in owners}
    for (prefix, code), owners in series.items():
        if not owners:
            owners |= {project for (doc, number), project in sub_projects.items() if doc in series_plans[prefix] and f"wp{number}" == code}
    for row in zenodo:
        value = row.value
        output_id = f"zenodo:{value.record_id}"
        links, delivered = zenodo_links[output_id]
        if (found := SERIES.match(value.title or "")) and len(owners := series[(plain(found[1]), code_key(found[2]) or "")]) == 1:
            links.add((next(iter(owners)), "series"))
        authors = tuple(
            (person_id, position, name, affiliation)
            for key, position, name, affiliation in output_authors.get(output_id, [])
            if (person_id := people.person_of(key))
        )
        output_url = f"https://doi.org/{value.doi}" if value.doi else None
        for initiative_id, basis in links:
            if value.publication_date:
                activity[initiative_id].add((value.publication_date, f"output ({basis})", value.title or "", output_url or ""))
            if basis != "description":
                derived.share("output", output_id, value.title or output_id, initiative_id, output_url, row.evidence)
                for person_id, *_ in authors:
                    entry = derived.involve(person_id, initiative_id, "author", row.evidence, None)
                    entry.outputs.add(f"{value.publication_date or ''} {value.title or ''}".strip()[:160])
        link = OutputLink(
            output_id=output_id,
            authors=authors,
            initiatives=merged_bases(links),
            plan_items=merged_bases(delivered),
            url=None,
            creators=len(value.person_names),
        )
        context.map(ZENODO_OUTPUTS, row, SourceRecord(link, row.evidence))
    def f1000_links(value: F1000Item) -> set[tuple[str, str]]:
        key = url_key(documents.url(value.item_path)) or url_key(f"https://f1000research.com/{value.item_path}")
        found = linked_outputs.get(key or "", set()) | named(value.title, value.subjects, value.description)
        return found | group_authors(value.person_names)

    by_doi: dict[str, list[SourceRecord[F1000Item]]] = defaultdict(list)
    for row in f1000:
        by_doi[(row.value.doi or row.value.item_path).lower()].append(row)
    for group in by_doi.values():
        row, *repeated = sorted(group, key=lambda item: item.value.item_path)
        for extra in repeated:
            context.exclude("duplicate_record", extra.evidence)
        value = row.value
        output_id = f"f1000:{slug(value.item_path)}"
        authors = tuple(
            (person_id, position, name, affiliation)
            for mention_key, position, name, affiliation in output_authors.get(output_id, [])
            if (person_id := people.person_of(mention_key))
        )
        links = {found for item in group for found in f1000_links(item.value)}
        output_url = documents.url(value.item_path)
        for initiative_id, basis in links:
            if value.date:
                activity[initiative_id].add((value.date, f"output ({basis})", value.title or "", output_url or ""))
            if basis != "description":
                derived.share("output", output_id, value.title or output_id, initiative_id, output_url, row.evidence)
                for person_id, *_ in authors:
                    entry = derived.involve(person_id, initiative_id, "author", row.evidence, None)
                    entry.outputs.add(f"{value.date or ''} {value.title or ''}".strip()[:160])
        link = OutputLink(output_id, authors, merged_bases(links), (), documents.url(value.item_path))
        context.map(F1000_OUTPUTS, row, SourceRecord(link, row.evidence))

    group_tools: dict[str, list[str]] = defaultdict(list)
    tool_aliases: list[tuple[list[re.Pattern[str]], str, set[str], set[str]]] = []
    for row in tool_admitted:
        value = row.value
        tagged: list[Linked] = []
        for tag, kind in [*((t, "platform") for t in value.elixir_platforms), *((t, "community") for t in value.elixir_communities)]:
            if initiative_id := initiatives.resolve(tag, kind):
                tagged.append((initiative_id, tag, "tag"))
            else:
                collected.counts["tool_tags_unresolved"] += 1
        domain_rows = domain_tools.get(value.biotools_id, [])
        if community := initiatives.by_claim.get(DOMAIN_COMMUNITY):
            tagged.extend((community, domain.value.domain, "community_domain") for domain in domain_rows)
        nodes = [(node_id, tag) for tag in value.elixir_nodes if (node_id := resolve_node(tag))]
        for node_id, _ in nodes:
            collected.cite(node_id, row.evidence)
        collected.counts["tool_tags_unresolved"] += len(value.elixir_nodes) - len(nodes)
        credits = [(person_id, name) for key, name in tool_people.get(value.biotools_id, []) if (person_id := people.person_of(key))]
        recommenders = tool_recommenders.get(value.biotools_id, set())
        for initiative_id, tag, basis in tagged:
            group_tools[initiative_id].append(value.name or value.biotools_id)
            if basis == "tag":
                derived.share("tool", f"tool:{value.biotools_id}", value.name or value.biotools_id, initiative_id, f"https://bio.tools/{value.biotools_id}", row.evidence)
        for person_id, _ in credits:
            derived.person_tools[person_id].add(value.name or value.biotools_id)
            for initiative_id in {i for i, _, _ in tagged} | {i for i, _ in recommenders}:
                derived.involve(person_id, initiative_id, "tool_credit", row.evidence, None).tools.add(value.name or value.biotools_id)
        link = CatalogueLink(
            item_id=f"tool:{value.biotools_id}",
            initiatives=tuple(dict.fromkeys(tagged)),
            nodes=tuple(dict.fromkeys(nodes)),
            topics=tuple(tool_topics.get(value.biotools_id, [])),
            people=tuple(dict.fromkeys(credits)),
            provider=None,
            recommended_by=tuple(sorted(f"{initiatives.identities[i].name} ({basis})" for i, basis in recommenders)),
        )
        context.map(TOOLS, row, SourceRecord(link, row.evidence + tuple(e for domain in domain_rows for e in domain.evidence)))
        tool_aliases.append(
            (
                tool_patterns(value.name or value.biotools_id, value.description),
                f"{value.name or value.biotools_id} (https://bio.tools/{value.biotools_id}; credited: {', '.join(dict.fromkeys(name for _, name in credits)) or 'nobody'})",
                {i for i, _, _ in tagged} | {i for i, _ in recommenders},
                {person_id for person_id, _ in credits},
            )
        )

    facet_rows = [(row.value.catalogue, row.value.facet, row.value.value, row.value.count) for row in facets]

    def facet_names(facet: str, counts: dict[str, Counter[str]]) -> dict[str, str]:
        return names_by_count([(c, v, n) for c, f, v, n in facet_rows if f == facet], counts)

    def counted(values: dict[str, list[list[str]]]) -> dict[str, Counter[str]]:
        return {catalogue: Counter(i for ids in lists for i in ids) for catalogue, lists in values.items()}

    node_names = facet_names(
        "node", counted({"events": [r.value.node_ids for r in events], "materials": [r.value.node_ids for r in materials]})
    )
    collection_names = facet_names(
        "collections",
        counted({"events": [r.value.collection_ids for r in events], "materials": [r.value.collection_ids for r in materials]}),
    )
    provider_names = facet_names(
        "content-provider",
        counted(
            {
                "events": [[r.value.content_provider_id] if r.value.content_provider_id else [] for r in events],
                "materials": [[r.value.content_provider_id] if r.value.content_provider_id else [] for r in materials],
            }
        ),
    )
    collection_initiatives = {
        identifier: (initiative_id, title)
        for identifier, title in collection_names.items()
        if (initiative_id := initiatives.resolve(collection_name(title)))
    }
    tess_nodes = {identifier: (node_id, name) for identifier, name in node_names.items() if (node_id := resolve_node(name))}

    def tess_link(item_id: str, node_ids: list[str], collection_ids: list[str], topic_list: list[str], provider: str | None) -> CatalogueLink:
        collected.counts["tess_node_ids_unnamed"] += sum(1 for i in node_ids if i not in tess_nodes)
        collected.counts["tess_collection_ids_unnamed"] += sum(1 for i in collection_ids if i not in collection_initiatives)
        return CatalogueLink(
            item_id=item_id,
            initiatives=tuple(
                dict.fromkeys(
                    (*collection_initiatives[i], f"https://tess.elixir-europe.org/collections/{i}")
                    for i in collection_ids
                    if i in collection_initiatives
                )
            ),
            nodes=tuple(dict.fromkeys(tess_nodes[i] for i in node_ids if i in tess_nodes)),
            topics=tuple(topic_list),
            people=(),
            provider=provider_names.get(provider) if provider else None,
            collections=tuple(sorted({collection_names[i] for i in collection_ids if i in collection_names})),
            collections_unnamed=sum(1 for i in collection_ids if i not in collection_names),
        )

    for row in events:
        value = row.value
        link = tess_link(f"tess_event:{value.tess_id}", value.node_ids, value.collection_ids, event_topics[value.tess_id], value.content_provider_id)
        context.map(EVENTS, row, SourceRecord(link, row.evidence))
    for row in materials:
        value = row.value
        link = tess_link(
            f"tess_material:{value.tess_id}", value.node_ids, value.collection_ids, material_topics[value.tess_id], value.content_provider_id
        )
        context.map(MATERIALS, row, SourceRecord(link, row.evidence))
    for row in reviews_rows:
        context.map(REVIEW_PAPERS, row)
    elixir_event_rows: dict[str, SourceRecord[ElixirEventRow]] = {}
    own_page_first = sorted(
        elixir_events, key=lambda row: page_url_key(documents.url(row.value.document), documents.redirects) != url_key(row.value.url)
    )
    for row in own_page_first:
        key = url_key(row.value.url) or slug(row.value.title)
        if key in elixir_event_rows:
            context.exclude("duplicate_record", row.evidence)
        else:
            elixir_event_rows[key] = row
    for key, row in sorted(elixir_event_rows.items()):
        url = row.value.url or documents.url(row.value.document)
        documents.located(row.value.document)
        linked = tuple((initiative_id, row.value.title, url or "") for initiative_id in phrases.find(row.value.title))
        for initiative_id, _, _ in linked:
            if row.value.start:
                held = "meeting held" if row.value.start <= SNAPSHOT_DATE else "meeting announced"
                activity[initiative_id].add((row.value.start, held, row.value.title, url or ""))
        context.map(ELIXIR_EVENTS, row, SourceRecord(EventLink(f"elixir_event:{slug(key)}", url, linked), row.evidence))
    for row, link in recommendation_links:
        context.map(RECOMMENDS, row, link)

    plan_info = {plan.value.plan_item_id: plan.value for plan in plan_records}
    for edge in collected.edges["works_on_plan_item"].values():
        plan = plan_info.get(edge.value.target)
        if plan:
            entry = derived.involve(edge.value.source, plan.initiative_id, "plan_item", edge.evidence, edge.value.located.url)
            entry.plan.add(f"{edge.value.role}: {plan.code + ' ' if plan.code else ''}{plan.label[:100]}")
            entry.leads_plan = entry.leads_plan or edge.value.role == "lead"
    for key, entry in list(derived.involved.items()):
        if entry.bases == {"tool_credit"} or key in removed_roles:
            collected.counts["involvements_dropped_tool_credit_only" if key not in removed_roles else "involvements_removed_by_correction"] += 1
            del derived.involved[key]
    def item_id(initiative_id: str, written: str | None) -> str | None:
        codes = [code for part in reversed(WORK_ITEM_CODE.findall(written or "")) if (code := code_key(part))]
        return next((found for code in codes if (found := plan_by_code.get((initiative_id, code)))), None)

    for row in plan_links:
        value = row.value
        owner = placement.owner(value.document, value.owner, False)
        linked = initiatives.resolve(value.linked_project) or phrases.one(value.linked_project) or placement.named_project(value.linked_project)
        if owner is None or linked is None or owner == linked:
            context.exclude("plan_link_unresolved", row.evidence)
            continue
        located = documents.located(value.document)
        own, other = item_id(owner, value.item), item_id(linked, value.linked_item)
        for record in (
            PlanLinkRecord(owner, linked, "stated", value.item, own, value.linked_item, other, value.relation, quote(row), located),
            PlanLinkRecord(linked, owner, "reverse", value.linked_item, other, value.item, own, value.relation, quote(row), located),
        ):
            context.map(PLAN_LINKED_TO, SourceRecord(record, row.evidence))
    derived.plan_totals.update(Counter(plan.value.initiative_id for plan in plan_records))
    initiative_people: dict[str, set[str]] = defaultdict(set)
    for person_id, initiative_id in derived.involved:
        initiative_people[initiative_id].add(person_id)
    delivered_items = {plan_item_id for _, delivered in zenodo_links.values() for plan_item_id, _ in delivered}
    for record in plan_records:
        item = record.value
        if item.plan_item_id in delivered_items:
            item = replace(item, status="delivered")
            collected.counts["plan_items_delivered"] += 1
        text = f"{item.label} {item.description or ''}"
        named_tools = tuple(
            label
            for patterns, label, linked, credited in tool_aliases
            if (item.initiative_id in linked or credited & initiative_people[item.initiative_id]) and any(p.search(text) for p in patterns)
        )
        collected.counts["plan_items_naming_tools"] += bool(named_tools)
        context.map(PLAN_ITEMS, SourceRecord(replace(item, tools=named_tools[:10]), record.evidence))
    for plan in plan_records:
        item = plan.value
        label = f"{item.code + ' ' if item.code else ''}{item.label[:100]}"
        for role, names in (("lead", item.leads), ("participant", item.participants)):
            for name in names:
                if node_id := resolve_node(name) or resolve_code_prefix(name.split("/")[-1].strip()):
                    derived.node_plan[(node_id, item.initiative_id, role)][label].add(name)
    for edge in collected.edges["related_to"].values():
        project, group = edge.value.source, edge.value.target
        if initiatives.identities[project].family == "project" and initiatives.identities[project].kind not in NOT_SHARING:
            derived.share("project", project, initiatives.identities[project].name, group, edge.value.located.url, edge.evidence)
    for (person_id, initiative_id), entry in list(derived.involved.items()):
        if entry.kinds & SHARING_LEADERS:
            derived.share("leader", person_id, people.identities[person_id].name, initiative_id, next(iter(entry.urls), None), entry.evidence)
    for row in corrections:
        value = row.value
        if value.property != "node":
            continue
        if value.subject not in people.identities or value.target not in BY_ID:
            context.exclude("correction_target_missing", row.evidence)
            continue
        if value.action == "remove":
            edges = collected.edges["in_node"]
            for key in [key for key, edge in edges.items() if (edge.value.source, edge.value.target) == (value.subject, value.target)]:
                del edges[key]
        else:
            collected.edge("in_node", EdgeLink(value.subject, value.target, correction_note(value), CORRECTED, None, "correction"), row.evidence)
        collected.counts["corrections_applied"] += 1
    past_pages = {primary_key.get(i) for i, entry in registry_of.items() if entry.status == "past"} - {None}
    person_nodes_found: dict[str, dict[str, None]] = defaultdict(dict)
    past_nodes: dict[str, dict[str, None]] = defaultdict(dict)
    for edge in collected.edges["in_node"].values():
        past = page_url_key(edge.value.located.url, documents.redirects) in past_pages
        (past_nodes if past else person_nodes_found)[edge.value.source][edge.value.target] = None
    for person_id, nodes in past_nodes.items():
        if person_id not in person_nodes_found:
            person_nodes_found[person_id] = nodes
        else:
            collected.counts["past_group_nodes_set_aside"] += len(set(nodes) - set(person_nodes_found[person_id]))
    for person_id, nodes in person_nodes_found.items():
        if not nodes or set(nodes) & INTERNATIONAL_NODES:
            continue
        identity = people.identities[person_id]
        for domain in identity.email_domains:
            country = CODES.get(domain.rsplit(".", 1)[-1].upper())
            if country and country not in nodes and BY_ID[country].kind == "member_node":
                collected.add_review(
                    review(
                        "value_conflict",
                        f"Sources place {identity.name} in {', '.join(BY_ID[n].name for n in nodes)}, but their email domain {domain} is in another country. Which is their Node?",
                        [person_id],
                        [identity.name],
                        [*(option(BY_ID[n].name, []) for n in nodes), option(BY_ID[country].name, [f"email domain {domain}"])],
                        "node",
                    )
                )
    person_organisations: dict[str, dict[str, None]] = defaultdict(dict)
    for edge in collected.edges["affiliated_with"].values():
        person_organisations[edge.value.source][organisations.identities[edge.value.target].name] = None
    persons = Persons(
        names={key: identity.name for key, identity in people.identities.items()},
        nodes={key: tuple(BY_ID[n].name for n in found) for key, found in person_nodes_found.items()},
        node_ids={key: tuple(found) for key, found in person_nodes_found.items()},
        organisations={key: tuple(found) for key, found in person_organisations.items()},
    )
    leaders = derived.leaders(persons)
    plan_labels: dict[str, list[str]] = defaultdict(list)
    for plan in plan_records:
        if plan.value.kind in SCOPE_PLAN_KINDS:
            plan_labels[plan.value.initiative_id].append(plan.value.label)
    for initiative_id, record in initiative_records.items():
        identity = initiatives.identities[initiative_id]
        newest = sorted(activity.get(initiative_id, set()), reverse=True)
        own = [item[0] for item in newest if (item[1].startswith("output") and item[1] != "output (description)") or item[1] == "meeting held"]
        scope = list(dict.fromkeys([*record.outcomes, *plan_labels[initiative_id][:40], *group_resources[initiative_id][:40], *group_tools[initiative_id][:40]]))
        record = replace(
            record,
            recent_activity=tuple(" | ".join(item) for item in newest[:ACTIVITY_ITEMS]),
            latest_own_activity=own[0] if own else None,
            latest_activity=newest[0][0] if newest else None,
            leaders=leaders.get(initiative_id, ()),
            limits=limits(identity.family, identity.kind, record.join_url, record.joining, record.status, record.period_status, record.end),
            scope="; ".join(scope)[:4000] or None,
        )
        initiative_records[initiative_id] = record
        context.map(INITIATIVES, SourceRecord(record, collected.cited(initiative_id)))
    for involvement, evidence in derived.records(persons):
        context.map(INVOLVED_IN, SourceRecord(involvement, evidence or collected.cited(involvement.initiative_id, limit=3)))
    node_links = [
        (edge.value.source, edge.value.target, edge.value.basis, edge.value.located.url, edge.evidence)
        for edge in collected.edges["takes_part_in"].values()
    ]
    periods = {key: (record.kind, record.start, record.end, record.period_status) for key, record in initiative_records.items()}
    site_named: dict[str, set[str]] = defaultdict(set)
    listing_nodes: set[str] = set()
    for document, claimed in placement.claimed.items():
        source = (documents.info[document].value.source or "") if document in documents.info else ""
        if source.startswith("node-") and (node_id := resolve_node(source[5:]) or CODES.get(source[5:].upper())):
            site_named[node_id] |= claimed
            if source in NODE_PROJECT_LISTINGS:
                listing_nodes.add(node_id)
    derived.node_sites = {node_id: ("listed", "not_listed") if node_id in listing_nodes else ("listed", None) for node_id in site_named}
    derived.site_named = site_named
    for involvement, evidence in derived.node_records(node_links, persons, periods):
        context.map(NODE_INVOLVED_IN, SourceRecord(involvement, evidence or collected.cited(involvement.initiative_id, limit=3)))
    families = {key: identity.family for key, identity in initiatives.identities.items()}
    for shared, evidence in derived.shared_work(families):
        context.map(SHARES_WORK_WITH, SourceRecord(shared, evidence or collected.cited(shared.source, limit=3)))
    collected.counts["involvements"] = len(derived.involved)
    for row, link in statement_links:
        context.map(SOURCE_STATEMENTS, row, link)
    for key in sorted(collected.edges["takes_part_in"]):
        context.map(TAKES_PART_IN, collected.edges["takes_part_in"][key])
    for key in sorted(collected.edges["related_to"]):
        context.map(RELATED_TO, collected.edges["related_to"][key])
    for key in sorted(collected.edges["part_of"]):
        context.map(PART_OF, collected.edges["part_of"][key])
    for key in sorted(collected.edges["in_node"]):
        context.map(IN_NODE, collected.edges["in_node"][key])
    for key in sorted(collected.edges["affiliated_with"]):
        context.map(AFFILIATED_WITH, collected.edges["affiliated_with"][key])
    for key in sorted(collected.edges["works_on_plan_item"]):
        context.map(WORKS_ON_PLAN_ITEM, collected.edges["works_on_plan_item"][key])

    emit_people(context, people, mention_evidence, collected)
    for identity in organisations.identities.values():
        collected.cite(identity.organisation_id, organisation_evidence.get(identity.organisation_id, set()))
        context.map(ORGANISATIONS, SourceRecord(identity, collected.cited(identity.organisation_id)))
    for left, right in organisations.candidates:
        names = [organisations.identities[left].name, organisations.identities[right].name]
        collected.add_review(
            review("organisation_match", f"Are '{names[0]}' and '{names[1]}' the same organisation?", [left, right], names, ["same", "different"])
        )
    for left, right in initiatives.candidates:
        names = [initiatives.identities[left].name, initiatives.identities[right].name]
        collected.add_review(
            review("initiative_match", f"Are '{names[0]}' and '{names[1]}' the same group or project?", [left, right], names, ["same", "different"])
        )
    node_list = tuple(
        e for record in documents.info.values() if url_key(record.value.url) == NODE_LIST_PAGE for e in record.evidence
    )
    for entry in NODES:
        context.map(ELIXIR_NODES, SourceRecord(entry, node_list + collected.cited(entry.node_id, limit=50)))
    for record in topics.values():
        context.map(TOPICS, record)
    for path in sorted(documents.used):
        context.map(SOURCE_DOCUMENTS, documents.info[path])
    for item in collected.reviews.values():
        evidence = decisions.evidence(item.review_id) + collected.cited(*item.subjects, limit=50)
        context.map(REVIEW_ITEMS, SourceRecord(decisions.resolved(item), evidence))

    counts = Counter(item.kind for item in collected.reviews.values())
    context.record_audit(
        "alignment",
        inputs="all selected sources",
        outputs="people, organisations, initiatives, plan items and review items",
        selection="Identity rules of ASSUMPTIONS.md; unclear matches and conflicting values become review items.",
        counts={
            "mentions": len(mentions),
            "people": len(people.identities),
            "ambiguous_names": len(people.ambiguous),
            "initiative_claims": len(claims) + len(role_claims),
            "initiatives_from_roles": len(role_claims),
            "initiatives_from_plan_owners": len(plan_claims),
            "initiatives": len(initiatives.identities),
            "registry_entries": len(entries),
            "resources": len(recommended),
            "tools_admitted": len(tool_admitted),
            "organisations": len(organisations.identities),
            "plan_items": len(plan_records),
            **{f"review_{kind}": count for kind, count in counts.items()},
            "decisions": len(decisions.rows),
            "decisions_applied": len(decisions.used),
            "decisions_without_item": len(set(decisions.rows) - decisions.used),
            **dict(collected.counts),
        },
    )


def at(values: list[str], index: int) -> str:
    return values[index] if index < len(values) else ""


def emit_people(context: RunContext, people: People, evidence: dict[str, tuple[Evidence, ...]], collected: Collected) -> None:
    for identity in people.identities.values():
        collected.cite(identity.person_id, (e for key in identity.mentions for e in evidence.get(key, ())))
        context.map(PEOPLE, SourceRecord(identity, collected.cited(identity.person_id)))
    for left, right in people.candidates:
        a, b = people.identities[left], people.identities[right]
        collected.add_review(
            review(
                "person_match",
                f"Are '{display_name(a.name)}' and '{display_name(b.name)}' the same person?",
                [left, right],
                [a.name, b.name],
                [f"{a.name} | {', '.join(a.source_kinds)}", f"{b.name} | {', '.join(b.source_kinds)}", "same", "different"],
            )
        )
