import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import TypeVar
from urllib.parse import urljoin

from biotope.graph import Evidence, RunContext, SourceRecord

from ..alignment.catalogues import collection_name, names_by_count, zenodo_record_id
from ..alignment.initiatives import Claim, Initiatives, resolve_initiatives
from ..alignment.keys import acronym_key, group_key, plain, url_key
from ..alignment.links import (
    CatalogueLink,
    DocumentInfo,
    EdgeLink,
    Located,
    OutputLink,
    ParticipationLink,
    InitiativeRecord,
    PlanItemRecord,
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
from ..alignment.names import digest, display_name, is_person_name, slug
from ..alignment.nodes import BY_ID, CODES, NODES, resolve_code_prefix, resolve_node
from ..alignment.organisations import resolve_organisations
from ..alignment.people import Mention, People, email_of, orcid_of, resolve_people
from ..alignment.reviews import Review, review, review_id
from ..mappings.catalogues import (
    EVENTS,
    F1000_OUTPUTS,
    MATERIALS,
    REVIEW_PAPERS,
    SOURCE_DOCUMENTS,
    TOOLS,
    TOPICS,
    ZENODO_OUTPUTS,
)
from ..mappings.entities import ELIXIR_NODES, ORGANISATIONS, PEOPLE, REVIEW_ITEMS
from ..mappings.initiatives import INITIATIVES, PARTICIPATIONS, RELATED_TO, SOURCE_STATEMENTS, TAKES_PART_IN
from ..mappings.people import AFFILIATED_WITH, HOLDS_ROLE, IN_NODE, LEADS_PLAN_ITEM
from ..mappings.plans import PLAN_ITEMS
from ..sources.catalogues.biotools.loader import load as load_biotools
from ..sources.catalogues.europepmc_reviews.loader import load as load_reviews
from ..sources.catalogues.f1000_items.loader import load as load_f1000
from ..sources.catalogues.tess_events.loader import load as load_events
from ..sources.catalogues.tess_facets.loader import load as load_facets
from ..sources.catalogues.tess_materials.loader import load as load_materials
from ..sources.catalogues.zenodo_records.loader import load as load_zenodo
from ..sources.cordis_participants_jsonl.records.loader import load as load_participants
from ..sources.cordis_projects_jsonl.records.loader import load as load_projects
from ..sources.data_sources_scraping_jsonl.scraping_index.loader import load as load_index
from ..sources.initiative_statements_jsonl.records.loader import load as load_statements
from ..sources.initiative_statements_jsonl.records.schema import InitiativeStatementRow
from ..sources.perun.export.loader import load as load_perun
from ..sources.perun.export_2.loader import load as load_perun_2
from ..sources.plan_items_jsonl.records.loader import load as load_plan_items
from ..sources.plan_items_jsonl.records.schema import PlanItemRow
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
ADVISORY_ROLE = re.compile(r"advis|\bexternal\b|\b(SAB|EAB|STAB)\b", re.I)
INFRASTRUCTURE_NAMES = ("elixir", "elixir europe", "elixir hub")
FUNDING_WORDS = re.compile(r"\b(fund|funded|funding|grant|financ|paid|salar|in[- ]kind|sponsor)", re.I)
ACRONYM_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{3,}")
GROUP_QUALIFIER = re.compile(r"community|platform|focus group|elixir", re.I)
DELIVERABLE_CODE = re.compile(r"\b([DM]\s?\d+\.\d+)\b")
PLAN_PROJECT_KINDS = frozenset({"work_package", "task", "deliverable", "milestone"})
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
        key = digest(link.source, link.target, link.located.document_id or "", link.role or "")
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


Row = TypeVar("Row", InitiativeStatementRow, RoleStatementRow, PlanItemRow)


def page_identity(url: str | None) -> str | None:
    return url.split("#", 1)[0].rstrip("/") if url else None


def current(context: RunContext, rows: list[SourceRecord[Row]], superseded: set[str]) -> list[SourceRecord[Row]]:
    kept: list[SourceRecord[Row]] = []
    for row in rows:
        if row.value.document in superseded:
            context.exclude("superseded_snapshot", row.evidence)
        else:
            kept.append(row)
    return kept


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


def work_codes(work_item: str | None) -> list[str]:
    return [found for found in (code_key(part) for part in WORK_ITEM_CODE.findall(work_item or "")) if found]


def funding(value: RoleStatementRow, evidence: str | None) -> str:
    if value.funding != "not_stated" and not FUNDING_WORDS.search(evidence or ""):
        return "not_stated"
    return value.funding


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
                kind=value.kind,
                coverage=value.coverage,
                url=base,
                links=tuple(absolute(base, link) for link in value.links),
            )
        )
    return claims


def run(context: RunContext) -> None:
    documents = read_documents(context)
    collected = Collected()
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
    roles = list(load_roles(context))
    plans = list(load_plan_items(context))
    superseded = documents.superseded({row.value.document for row in [*statements, *roles, *plans]})
    statements = current(context, statements, superseded)
    roles = current(context, roles, superseded)
    plans = current(context, plans, superseded)
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

    claims = initiative_claims(statements, documents)
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
    for row in statements:
        value = row.value
        initiative_id = initiatives.by_claim[f"statement:{value.id}"]
        identity = initiatives.identities[initiative_id]
        url = documents.url(value.document)
        located = documents.located(value.document)
        own = url_key(url)
        own = documents.redirects.get(own, own) if own else None
        stated[initiative_id].append(
            Stated(
                url=url,
                coverage=value.coverage,
                primary=bool(identity.pages) and own is not None and f"https://{own}" == identity.pages[0],
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
            collected.edge("takes_part_in", EdgeLink(node_id, initiative_id, name, located), row.evidence)
        if len(stated_nodes) >= 2:
            node_sets[initiative_id][frozenset(stated_nodes)].append(url)
        for name in value.related:
            related = initiatives.resolve(name)
            if related is None:
                collected.counts["statement_related_unresolved"] += 1
            elif related != initiative_id:
                collected.edge("related_to", EdgeLink(initiative_id, related, name, located), row.evidence)
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

    initiative_records: dict[str, InitiativeRecord] = {}
    for identity in initiatives.identities.values():
        record, conflicts = merge_initiative(
            identity, stated.get(identity.initiative_id, []), funded.get(identity.initiative_id), decisions
        )
        for conflict in conflicts:
            collected.add_review(conflict)
        initiative_records[identity.initiative_id] = record

    planned: dict[tuple[str, str], list[PlannedItem]] = defaultdict(list)
    plan_rows: dict[tuple[str, str], list[SourceRecord[PlanItemRow]]] = defaultdict(list)
    for row in plans:
        value = row.value
        prefer = value.kind in PLAN_PROJECT_KINDS
        initiative_id = initiatives.by_claim.get(f"plan:{value.id}") or placement.owner(value.document, value.owner, prefer)
        if initiative_id is None:
            context.exclude("plan_owner_unresolved", row.evidence)
            continue
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
            leads=tuple(value.leads),
            participants=tuple(value.participants),
            effort=value.effort,
            link=value.link,
            url=documents.url(value.document),
            evidence=quote(row),
            topics=topic_ids(value.topics),
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
    for row in roles:
        value = row.value
        if is_person_name(value.person_name):
            mention(f"role:{value.id}", value.person_name, "role_statement", row.evidence, email=email_of(value.email))
    plan_leads: list[tuple[str, str, SourceRecord[PlanItemRow]]] = []
    for row in plans:
        if row.value.id not in plan_of_row:
            continue
        for index, lead in enumerate(row.value.leads):
            name = re.split(r"[/(]", PARTNER_PREFIX.sub("", lead), maxsplit=1)[0].strip()
            if is_person_name(name):
                key = mention(f"plan:{row.value.id}:{index}", name, "plan_item", row.evidence)
                plan_leads.append((key, lead, row))
    tool_admitted = [row for row in biotools if row.value.elixir_nodes or row.value.elixir_platforms or row.value.elixir_communities]
    for row in biotools:
        if not (row.value.elixir_nodes or row.value.elixir_platforms or row.value.elixir_communities):
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
        for index, name in enumerate(value.person_names):
            orcid = orcid_of(value.orcids[index]) if index < len(value.orcids) else None
            if is_person_name(name) or orcid:
                key = mention(f"zenodo:{value.record_id}:{index}", name, "zenodo", row.evidence, orcid=orcid)
                affiliation = value.creator_affiliations[index] if index < len(value.creator_affiliations) else ""
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

    organisations = resolve_organisations(
        [(row.value.organisation, row.value.country, row.value.activity_type) for row in participants],
        [value.affiliation for row in roles if (value := row.value).affiliation and is_person_name(value.person_name)]
        + [row.value.place for row in roles if row.value.place_kind == "organisation"],
        [],
    )
    if decided_organisations := decisions.same("organisation_match", organisations.candidates):
        organisations = resolve_organisations(
            [(row.value.organisation, row.value.country, row.value.activity_type) for row in participants],
            [value.affiliation for row in roles if (value := row.value).affiliation and is_person_name(value.person_name)]
            + [row.value.place for row in roles if row.value.place_kind == "organisation"],
            decided_organisations,
        )
    organisation_evidence: dict[str, set[Evidence]] = defaultdict(set)
    for row in roles:
        value = row.value
        for name in (value.affiliation, value.place if value.place_kind == "organisation" else None):
            if name and (organisation_id := organisations.of(name)):
                organisation_evidence[organisation_id].update(row.evidence)
    for row in participants:
        if organisation_id := organisations.of(row.value.organisation):
            organisation_evidence[organisation_id].update(row.evidence)
        initiative_id = initiatives.by_claim.get(f"cordis:{row.value.grant_id}")
        if organisation_id and initiative_id:
            context.map(
                PARTICIPATIONS,
                row,
                SourceRecord(ParticipationLink(organisation_id, initiative_id, documents.located(row.value.document)), row.evidence),
            )

    work_leads: dict[tuple[str, str | None, str], set[str]] = defaultdict(set)
    for row in roles:
        initiative_id, work_item = role_initiative.get(row.value.id, (None, None))
        on_project_page = "/eu-projects/" in (documents.url(row.value.document) or "")
        if row.value.role_kind == "task_lead" and on_project_page and (codes := work_codes(work_item)):
            work_leads[(row.value.document, initiative_id, "/".join(codes))].add(row.value.person_name)
    lead_sets: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    person_nodes: dict[str, dict[str, set[str | None]]] = defaultdict(lambda: defaultdict(set))
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
        codes = work_codes(work_item)
        crowded = bool(codes) and len(work_leads[(value.document, initiative_id, "/".join(codes))]) > MAX_WORK_LEADS
        kind = role_kind(value, quote(row), crowded)
        collected.counts["crowded_work_leads_as_participants"] += kind != value.role_kind and crowded
        context.map(
            HOLDS_ROLE,
            row,
            SourceRecord(
                RoleLink(person_id, initiative_id, work_item, kind, funding(value, quote(row)), quote(row), located),
                row.evidence,
            ),
        )
        if work_item and kind in WORK_LEADS and codes:
            tried = [f"{codes[0]}/{codes[-1]}", codes[-1]] if len(codes) > 1 else [codes[0]]
            plan_item_id = next((found for code in tried if (found := plan_by_code.get((initiative_id, code)))), None)
            if plan_item_id:
                collected.edge("leads_plan_item", EdgeLink(person_id, plan_item_id, value.person_name, located), row.evidence)
            if kind in ("work_package_lead", "task_lead"):
                lead_sets[(initiative_id, f"lead of {tried[0].upper()}")][value.document].add(person_id)
        elif not work_item and kind in LEADS:
            lead_sets[(initiative_id, "leads")][value.document].add(person_id)
    for key, lead, row in plan_leads:
        person_id = people.person_of(key)
        plan_item_id = plan_of_row.get(row.value.id)
        if person_id and plan_item_id:
            located = documents.located(row.value.document)
            collected.edge("leads_plan_item", EdgeLink(person_id, plan_item_id, lead, located), row.evidence)
            if node_id := node_in(lead):
                collected.edge("in_node", EdgeLink(person_id, node_id, lead, located), row.evidence)

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

    for record in plan_records:
        context.map(PLAN_ITEMS, record)

    grant_initiative = {row.value.grant_id: initiatives.by_claim[f"cordis:{row.value.grant_id}"] for row in projects}
    acronym_index: dict[str, set[str]] = defaultdict(set)
    group_index: dict[str, set[str]] = defaultdict(set)
    for identity in initiatives.identities.values():
        if identity.family == "project" and (acronym := acronym_key(identity.acronym)):
            acronym_index[acronym].add(identity.initiative_id)
        if identity.kind in ("community", "platform", "focus_group"):
            for alias in identity.aliases:
                group_index[group_key(alias)].add(identity.initiative_id)

    def named(title: str | None, keywords: list[str]) -> set[tuple[str, str]]:
        found: set[tuple[str, str]] = set()
        for token in [*ACRONYM_TOKEN.findall(title or ""), *keywords]:
            key = acronym_key(token) if sum(char.isupper() for char in token) >= 2 else None
            if key and len(acronym_index.get(key, set())) == 1:
                found.add((next(iter(acronym_index[key])), "named"))
        for keyword in keywords:
            key = group_key(keyword)
            qualified = GROUP_QUALIFIER.search(keyword)
            if key and qualified and len(group_index.get(key, set())) == 1:
                found.add((next(iter(group_index[key])), "named"))
        return found

    for row in zenodo:
        value = row.value
        output_id = f"zenodo:{value.record_id}"
        links = set(linked_outputs.get(output_id, set()))
        links |= {(grant_initiative[code], "grant") for code in value.grant_codes if code in grant_initiative}
        links |= named(value.title, value.keywords)
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
                    if len(words & titled) >= max(2, len(words) / 2)
                ]
                if len(matches) == 1:
                    delivered.add((matches[0][0], "code"))
                    outputs_of_plan[output_id].add(matches[0])
        links |= {(initiative_id, "deliverable") for _, initiative_id in outputs_of_plan.get(output_id, set())}
        authors = tuple(
            (person_id, position, name, affiliation)
            for key, position, name, affiliation in output_authors.get(output_id, [])
            if (person_id := people.person_of(key))
        )
        link = OutputLink(
            output_id=output_id,
            authors=authors,
            initiatives=merged_bases(links),
            plan_items=merged_bases(delivered),
            url=None,
        )
        context.map(ZENODO_OUTPUTS, row, SourceRecord(link, row.evidence))
    for row in f1000:
        value = row.value
        output_id = f"f1000:{slug(value.item_path)}"
        key = url_key(f"https://f1000research.com/{value.item_path}")
        authors = tuple(
            (person_id, position, name, affiliation)
            for mention_key, position, name, affiliation in output_authors.get(output_id, [])
            if (person_id := people.person_of(mention_key))
        )
        url = documents.url(value.item_path)
        key = url_key(url) or key
        links = linked_outputs.get(key or "", set()) | named(value.title, value.subjects)
        link = OutputLink(output_id, authors, merged_bases(links), (), url)
        context.map(F1000_OUTPUTS, row, SourceRecord(link, row.evidence))

    for row in tool_admitted:
        value = row.value
        tagged: list[tuple[str, str]] = []
        for tag, kind in [*((t, "platform") for t in value.elixir_platforms), *((t, "community") for t in value.elixir_communities)]:
            if initiative_id := initiatives.resolve(tag, kind):
                tagged.append((initiative_id, tag))
            else:
                collected.counts["tool_tags_unresolved"] += 1
        nodes = [(node_id, tag) for tag in value.elixir_nodes if (node_id := resolve_node(tag))]
        for node_id, _ in nodes:
            collected.cite(node_id, row.evidence)
        collected.counts["tool_tags_unresolved"] += len(value.elixir_nodes) - len(nodes)
        credits = [(person_id, name) for key, name in tool_people.get(value.biotools_id, []) if (person_id := people.person_of(key))]
        link = CatalogueLink(
            item_id=f"tool:{value.biotools_id}",
            initiatives=tuple(dict.fromkeys(tagged)),
            nodes=tuple(dict.fromkeys(nodes)),
            topics=tuple(tool_topics.get(value.biotools_id, [])),
            people=tuple(dict.fromkeys(credits)),
            provider=None,
        )
        context.map(TOOLS, row, SourceRecord(link, row.evidence))

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
            initiatives=tuple(dict.fromkeys(collection_initiatives[i] for i in collection_ids if i in collection_initiatives)),
            nodes=tuple(dict.fromkeys(tess_nodes[i] for i in node_ids if i in tess_nodes)),
            topics=tuple(topic_list),
            people=(),
            provider=provider_names.get(provider) if provider else None,
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

    for initiative_id, record in initiative_records.items():
        context.map(INITIATIVES, SourceRecord(record, collected.cited(initiative_id)))
    for row, link in statement_links:
        context.map(SOURCE_STATEMENTS, row, link)
    for key in sorted(collected.edges["takes_part_in"]):
        context.map(TAKES_PART_IN, collected.edges["takes_part_in"][key])
    for key in sorted(collected.edges["related_to"]):
        context.map(RELATED_TO, collected.edges["related_to"][key])
    for key in sorted(collected.edges["in_node"]):
        context.map(IN_NODE, collected.edges["in_node"][key])
    for key in sorted(collected.edges["affiliated_with"]):
        context.map(AFFILIATED_WITH, collected.edges["affiliated_with"][key])
    for key in sorted(collected.edges["leads_plan_item"]):
        context.map(LEADS_PLAN_ITEM, collected.edges["leads_plan_item"][key])

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
            "organisations": len(organisations.identities),
            "plan_items": len(plan_records),
            **{f"review_{kind}": count for kind, count in counts.items()},
            "decisions": len(decisions.rows),
            "decisions_applied": len(decisions.used),
            "decisions_without_item": len(set(decisions.rows) - decisions.used),
            **dict(collected.counts),
        },
    )


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
