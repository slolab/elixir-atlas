from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .names import display_name, name_key, possibly_same, slug


@dataclass(frozen=True)
class Mention:
    key: str
    name: str
    source_kind: str
    orcid: str | None = None
    email: str | None = None
    perun_account: str | None = None
    perun_organisation: str | None = None


@dataclass(frozen=True)
class PersonIdentity:
    person_id: str
    name: str
    name_variants: tuple[str, ...]
    orcids: tuple[str, ...]
    email_domains: tuple[str, ...]
    in_perun: bool
    perun_organisation: str | None
    source_kinds: tuple[str, ...]
    identity_basis: tuple[str, ...]
    mentions: tuple[str, ...]


@dataclass
class People:
    by_mention: dict[str, str] = field(default_factory=dict[str, str])
    identities: dict[str, PersonIdentity] = field(default_factory=dict[str, PersonIdentity])
    ambiguous: dict[str, tuple[str, ...]] = field(default_factory=dict[str, tuple[str, ...]])
    candidates: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])

    def person_of(self, mention: str) -> str | None:
        return self.by_mention.get(mention)


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def orcid_of(value: str | None) -> str | None:
    if not value:
        return None
    tail = value.strip().rstrip("/").rsplit("/", 1)[-1].upper()
    return tail if len(tail) == 19 and tail.count("-") == 3 else None


def email_of(value: str | None) -> str | None:
    if not value or "@" not in value:
        return None
    return value.strip().lower().removeprefix("mailto:")


def compatible(left: str, right: str) -> bool:
    a, b = name_key(left), name_key(right)
    if a == b or possibly_same(a, b) or possibly_same(b, a):
        return True
    small, large = sorted((set(a.split()), set(b.split())), key=len)
    return bool(small) and small <= large


def resolve_people(mentions: list[Mention], same: list[tuple[str, str]]) -> People:
    accounts: dict[str, str] = {}
    for mention in mentions:
        if mention.perun_account and mention.email:
            accounts.setdefault(mention.email, mention.perun_account)
    canonical = {
        m.perun_account: accounts.get(m.email, m.perun_account) if m.email else m.perun_account
        for m in mentions
        if m.perun_account
    }
    by_mention = {mention.key: mention for mention in mentions}
    rejected: list[tuple[str, str]] = []
    by_key: dict[str, list[Mention]] = defaultdict(list)
    for mention in sorted(mentions, key=lambda m: m.key):
        by_key[name_key(mention.name)].append(mention)
    union = UnionFind()
    reasons: list[tuple[str, str]] = []
    ambiguous: dict[str, tuple[str, ...]] = {}
    for key, group in by_key.items():
        orcids = {m.orcid for m in group if m.orcid}
        perun = {canonical[m.perun_account] for m in group if m.perun_account}
        if len(orcids) > 1 or len(perun) > 1:
            ambiguous[key] = tuple(sorted(orcids | perun))
            for mention in group:
                anchor = mention.orcid or (canonical[mention.perun_account] if mention.perun_account else None)
                union.union(mention.key, f"{key}#{anchor}" if anchor else f"{key}#unresolved")
            continue
        for mention in group:
            union.union(mention.key, f"{key}#")
            reasons.append((mention.key, "exact_name" if len(group) > 1 else "single_mention"))
    reordered: dict[frozenset[str], set[str]] = defaultdict(set)
    for key in by_key:
        if key not in ambiguous and len(set(key.split())) >= 3:
            reordered[frozenset(key.split())].add(key)
    for keys in reordered.values():
        if len(keys) == 2:
            left, right = sorted(keys)
            union.union(f"{left}#", f"{right}#")
            reasons.append((by_key[left][0].key, "name_order"))
    for attribute in ("orcid", "email"):
        first: dict[str, str] = {}
        for mention in mentions:
            value = getattr(mention, attribute)
            if value:
                if value in first:
                    if union.find(first[value]) == union.find(mention.key):
                        continue
                    if not compatible(by_mention[first[value]].name, mention.name):
                        rejected.append((first[value], mention.key))
                        continue
                    reasons.append((mention.key, attribute))
                    union.union(first[value], mention.key)
                else:
                    first[value] = mention.key
    for left, right in same:
        if left in union.parent and right in union.parent:
            union.union(left, right)
            reasons.append((left, "decision"))
    basis: dict[str, set[str]] = defaultdict(set)
    for node, reason in reasons:
        basis[union.find(node)].add(reason)
    clusters: dict[str, list[Mention]] = defaultdict(list)
    for mention in mentions:
        clusters[union.find(mention.key)].append(mention)
    people = People(ambiguous=ambiguous)
    taken: set[str] = set()
    for root in sorted(clusters):
        group = clusters[root]
        names = Counter(display_name(m.name) for m in group)
        name = sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        base = f"person:{slug(name_key(name))}"
        person_id = base
        counter = 2
        while person_id in taken:
            person_id = f"{base}-{counter}"
            counter += 1
        taken.add(person_id)
        kinds = {m.source_kind for m in group}
        why = basis.get(root, set()) - ({"single_mention"} if len(group) > 1 else set())
        perun = [m for m in group if m.perun_account]
        people.identities[person_id] = PersonIdentity(
            person_id=person_id,
            name=name,
            name_variants=tuple(sorted(names)),
            orcids=tuple(sorted({m.orcid for m in group if m.orcid})),
            email_domains=tuple(sorted({m.email.rsplit("@", 1)[1] for m in group if m.email})),
            in_perun=bool(perun),
            perun_organisation=next((m.perun_organisation for m in perun if m.perun_organisation), None),
            source_kinds=tuple(sorted(kinds)),
            identity_basis=tuple(sorted(why or {"single_mention"})),
            mentions=tuple(sorted(m.key for m in group)),
        )
        for mention in group:
            people.by_mention[mention.key] = person_id
    pairs = set(candidate_pairs(people))
    for left, right in rejected:
        a, b = people.by_mention[left], people.by_mention[right]
        shared_word = set(name_key(people.identities[a].name).split()) & set(name_key(people.identities[b].name).split())
        if a != b and shared_word:
            pairs.add((min(a, b), max(a, b)))
    people.candidates = sorted(pairs)
    return people


def candidate_pairs(people: People) -> list[tuple[str, str]]:
    by_surname: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for person_id, identity in people.identities.items():
        for variant in identity.name_variants:
            tokens = name_key(variant).split()
            if tokens:
                by_surname[tokens[-1]].append((name_key(variant), person_id))
                by_surname[f"first:{tokens[0]}"].append((name_key(variant), person_id))
    pairs: set[tuple[str, str]] = set()
    for entries in by_surname.values():
        if len(entries) > 200:
            continue
        for index, (left_key, left_id) in enumerate(entries):
            for right_key, right_id in entries[index + 1 :]:
                if left_id != right_id and possibly_same(left_key, right_key):
                    pairs.add((min(left_id, right_id), max(left_id, right_id)))
    by_tokens: dict[frozenset[str], set[str]] = defaultdict(set)
    for person_id, identity in people.identities.items():
        for variant in identity.name_variants:
            by_tokens[frozenset(name_key(variant).split())].add(person_id)
    for ids in by_tokens.values():
        ordered = sorted(ids)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                pairs.add((left, right))
    shared: dict[str, list[str]] = defaultdict(list)
    for person_id, identity in people.identities.items():
        if name_key(identity.name) in people.ambiguous:
            shared[name_key(identity.name)].append(person_id)
    for ids in shared.values():
        for index, left in enumerate(sorted(ids)):
            for right in sorted(ids)[index + 1 :]:
                pairs.add((left, right))
    return sorted(pairs)
