from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import permutations
from urllib.parse import parse_qs, urlparse

from biotope.graph import Evidence

from .links import InvolvementRecord, NodeInvolvementRecord, SharedWork

LEADERSHIP = ("co_lead", "lead", "chair", "coordinator", "deputy", "liaison", "work_package_lead", "task_lead")
LEADER_ORDER = ("co_lead", "lead", "chair", "coordinator", "liaison", "deputy", "work_package_lead", "task_lead")
SHARING_LEADERS = frozenset(LEADERSHIP) - {"liaison"}
MAX_SHARING_GROUPS = 8
NODE_PEOPLE = 25
NOT_SHARING = frozenset({"programme_area", "infrastructure"})
GROUP_LIMIT = (
    "Membership: member lists are not public. The people named here are those public pages name (co-leads, liaisons, "
    "election candidates, plan-item people, authors); they are a lower bound, not the membership."
)
KIND_LIMITS = {
    "eu_project": "Grant agreement: the grant agreement, its description of work and each partner's effort (person-months) "
    "are not public; CORDIS gives beneficiaries, costs and EU contributions, and task roles come from the project's public "
    "pages and deliverables.",
    "commissioned_service": "Funding: no public page states whether each Node's contribution is funded or in-kind, or what "
    "each Node receives, unless a role's funding says so.",
}
NODE_LIMITS = (
    "Commitments: what the Node committed to, its effort, and whether its part is funded or in-kind are not public unless a "
    "plan item's effort, a role's funding or an EU beneficiary's contribution states it."
)
PEOPLE_LIMIT = (
    "Time and pay: no public source gives individuals' time, effort or pay unless a plan item's effort or a role's funding "
    "states it; an organisation's EU funding does not show that a named person is paid."
)
COVERAGE = (
    "Coverage: the Atlas collected the ELIXIR and Node websites, Zenodo, F1000Research, CORDIS, bio.tools and TeSS, not "
    "FAIRsharing, RDMkit, Slack, mailing lists, meeting minutes or documents behind a login; absence here does not prove absence."
)


@dataclass
class Involvement:
    roles: set[str] = field(default_factory=set[str])
    kinds: set[str] = field(default_factory=set[str])
    plan: set[str] = field(default_factory=set[str])
    outputs: set[str] = field(default_factory=set[str])
    tools: set[str] = field(default_factory=set[str])
    bases: set[str] = field(default_factory=set[str])
    urls: list[str] = field(default_factory=list[str])
    leads_plan: bool = False
    evidence: set[Evidence] = field(default_factory=set[Evidence])


@dataclass
class Shared:
    name: str
    groups: set[str] = field(default_factory=set[str])
    url: str | None = None
    evidence: set[Evidence] = field(default_factory=set[Evidence])


@dataclass
class People:
    names: dict[str, str]
    nodes: dict[str, tuple[str, ...]]
    node_ids: dict[str, tuple[str, ...]]
    organisations: dict[str, tuple[str, ...]]


@dataclass
class Derived:
    involved: dict[tuple[str, str], Involvement] = field(default_factory=lambda: defaultdict(Involvement))
    shared: dict[tuple[str, str], Shared] = field(default_factory=dict[tuple[str, str], Shared])
    beneficiaries: dict[tuple[str, str], set[str]] = field(default_factory=lambda: defaultdict(set))
    node_plan: dict[tuple[str, str, str], dict[str, set[str]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    plan_totals: dict[str, int] = field(default_factory=dict[str, int])
    person_tools: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    node_sites: dict[str, tuple[str, str | None]] = field(default_factory=dict[str, tuple[str, str | None]])
    site_named: dict[str, set[str]] = field(default_factory=dict[str, set[str]])

    def involve(self, person_id: str, initiative_id: str, basis: str, evidence: Iterable[Evidence], url: str | None) -> Involvement:
        entry = self.involved[(person_id, initiative_id)]
        entry.bases.add(basis)
        if url and url not in entry.urls:
            entry.urls.append(url)
        entry.evidence.update(list(evidence)[:3])
        return entry

    def role(self, person_id: str, initiative_id: str, kind: str, role: str, work_item: str | None, evidence: Iterable[Evidence], url: str | None) -> None:
        entry = self.involve(person_id, initiative_id, "candidate" if kind == "candidate" else "role", evidence, url)
        entry.roles.add(f"{kind}: {role}" + (f" ({work_item})" if work_item else ""))
        entry.kinds.add(kind)

    def share(self, via: str, item_id: str, name: str, group_id: str, url: str | None, evidence: Iterable[Evidence]) -> None:
        entry = self.shared.setdefault((via, item_id), Shared(name, url=url))
        entry.groups.add(group_id)
        entry.url = entry.url or url
        entry.evidence.update(list(evidence)[:2])

    def records(self, people: People) -> list[tuple[InvolvementRecord, tuple[Evidence, ...]]]:
        found: list[tuple[InvolvementRecord, tuple[Evidence, ...]]] = []
        for (person_id, initiative_id), entry in sorted(self.involved.items()):
            record = InvolvementRecord(
                person_id=person_id,
                initiative_id=initiative_id,
                leadership=bool(entry.kinds & set(LEADERSHIP)) or entry.leads_plan,
                roles=tuple(sorted(entry.roles, key=rank)),
                plan_items=tuple(sorted(entry.plan)),
                outputs=tuple(sorted(entry.outputs, reverse=True)[:10]),
                tools=(*(f"{tool} [this initiative]" for tool in sorted(entry.tools)), *sorted(self.person_tools.get(person_id, set()) - entry.tools))[:30],
                nodes=people.nodes.get(person_id, ()),
                organisations=people.organisations.get(person_id, ()),
                bases=tuple(sorted(entry.bases)),
                source_urls=tuple(entry.urls[:5]),
            )
            found.append((record, tuple(sorted(entry.evidence, key=lambda e: (e.artifact, e.location)))[:20]))
        return found

    def leaders(self, people: People) -> dict[str, tuple[str, ...]]:
        rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for (person_id, initiative_id), entry in self.involved.items():
            kinds = [kind for kind in LEADER_ORDER if kind in entry.kinds]
            if kinds:
                nodes = ", ".join(people.nodes.get(person_id, ()))
                name = people.names[person_id]
                rows[initiative_id].append((LEADER_ORDER.index(kinds[0]), f"{name} ({', '.join(kinds)}{'; ' + nodes if nodes else ''})"))
        return {key: tuple(text for _, text in sorted(found))[:30] for key, found in rows.items()}

    def node_records(
        self,
        links: Iterable[tuple[str, str, str, str | None, tuple[Evidence, ...]]],
        people: People,
        periods: dict[str, tuple[str, str | None, str | None, str | None]],
    ) -> list[tuple[NodeInvolvementRecord, tuple[Evidence, ...]]]:
        evidence: dict[tuple[str, str], set[Evidence]] = defaultdict(set)
        bases: dict[tuple[str, str], set[str]] = defaultdict(set)
        sources: dict[tuple[str, str], list[str]] = defaultdict(list)
        for node_id, initiative_id, basis, url, cited in links:
            bases[(node_id, initiative_id)].add(basis)
            evidence[(node_id, initiative_id)].update(cited[:2])
            if url and url not in sources[(node_id, initiative_id)]:
                sources[(node_id, initiative_id)].append(url)
        named: dict[tuple[str, str], list[tuple[bool, str]]] = defaultdict(list)
        for (person_id, initiative_id), entry in self.involved.items():
            if not entry.bases & {"role", "plan_item"} or entry.kinds == {"candidate"}:
                continue
            for node_id in people.node_ids.get(person_id, ()):
                for text in entry.plan:
                    role, _, label = text.partition(": ")
                    self.node_plan[(node_id, initiative_id, role)][label].add(people.names[person_id])
                parts = [", ".join(sorted(entry.roles, key=rank)), "; ".join(sorted(entry.plan)[:6])]
                leader = bool(entry.kinds & set(LEADERSHIP)) or entry.leads_plan
                named[(node_id, initiative_id)].append((not leader, f"{people.names[person_id]}: {'; '.join(p for p in parts if p)}"))
                bases[(node_id, initiative_id)].add("people")
                evidence[(node_id, initiative_id)].update(list(entry.evidence)[:2])
        found: list[tuple[NodeInvolvementRecord, tuple[Evidence, ...]]] = []
        for key in sorted(bases):
            node_id, initiative_id = key
            kind, start, end, status = periods[initiative_id]
            leads = self.node_plan.get((node_id, initiative_id, "lead"), {})
            works = {label: via for label, via in self.node_plan.get((node_id, initiative_id, "participant"), {}).items() if label not in leads}
            total = self.plan_totals.get(initiative_id, 0)
            record = NodeInvolvementRecord(
                node_id=node_id,
                initiative_id=initiative_id,
                bases=tuple(sorted(bases[key])),
                listed_on_own_page="own_page" in bases[key],
                initiative_kind=kind,
                period=f"{start or '?'} to {end or '?'}" if start or end else None,
                period_status=status,
                beneficiaries=tuple(sorted(self.beneficiaries.get(key, set()))),
                people=tuple(text for _, text in sorted(named.get(key, [])))[:NODE_PEOPLE],
                node_site=self.node_site(node_id, initiative_id),
                limits=NODE_LIMITS,
                plan_summary=f"Leads {len(leads)} of the {total} plan items; works on {len(works)} more" if total else None,
                leads_plan_items=listed(leads),
                works_on_plan_items=listed(works),
                sources=tuple(sources[key][:6]),
            )
            found.append((record, tuple(sorted(evidence.get(key, set()), key=lambda e: (e.artifact, e.location)))[:20]))
        return found

    def node_site(self, node_id: str, initiative_id: str) -> str | None:
        listed, otherwise = self.node_sites.get(node_id, ("listed", None))
        return listed if initiative_id in self.site_named.get(node_id, set()) else otherwise

    def shared_work(self, family: dict[str, str]) -> list[tuple[SharedWork, tuple[Evidence, ...]]]:
        found: list[tuple[SharedWork, tuple[Evidence, ...]]] = []
        for (via, item_id), entry in sorted(self.shared.items()):
            groups = sorted(group for group in entry.groups if family.get(group) == "group")
            if not 2 <= len(groups) <= MAX_SHARING_GROUPS:
                continue
            evidence = tuple(sorted(entry.evidence, key=lambda e: (e.artifact, e.location)))[:6]
            for source, target in permutations(groups, 2):
                found.append((SharedWork(source, target, via, entry.name, item_id, entry.url), evidence))
        return found


def listed(items: dict[str, set[str]]) -> tuple[str, ...]:
    return tuple(f"{label} (via {', '.join(sorted(via))})" for label, via in sorted(items.items()))[:40]


def rank(role: str) -> int:
    kind = role.split(":", 1)[0]
    return LEADER_ORDER.index(kind) if kind in LEADER_ORDER else len(LEADER_ORDER)


def limits(family: str, kind: str, join_url: str | None, joining: str | None, status: str | None, period: str | None, end: str | None) -> tuple[str, ...]:
    found = [GROUP_LIMIT] if family == "group" else []
    found += [KIND_LIMITS[kind]] if kind in KIND_LIMITS else []
    if join_url and not joining:
        group = parse_qs(urlparse(join_url).query).get("group", [""])[0]
        found.append(
            "Joining: its page gives no joining text; the join button (join_url) opens the Life Science Login registrar"
            + (f" to request membership of the ELIXIR group '{group}'" if group else "")
            + ". The Atlas holds no other joining procedure for it."
        )
    if period == "ended" and status != "completed":
        found.append(
            f"Status: its end date ({end}) has passed"
            + (" although a source still calls it current" if status == "current" else "")
            + "; no collected source states that it was completed or extended."
        )
    return (*found, PEOPLE_LIMIT, COVERAGE)
