import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .keys import plain
from .names import slug
from .people import UnionFind

LEGAL = re.compile(r"\b(vzw|ev|e v|gmbh|ltd|limited|sa|srl|bv|ab|oy|asbl|aisbl|fondation|stichting|associacao|ug|plc|inc)\b")


@dataclass(frozen=True)
class OrganisationIdentity:
    organisation_id: str
    name: str
    name_variants: tuple[str, ...]
    country: str | None
    activity_type: str | None


@dataclass
class Organisations:
    by_name: dict[str, str] = field(default_factory=dict[str, str])
    identities: dict[str, OrganisationIdentity] = field(default_factory=dict[str, OrganisationIdentity])
    candidates: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])

    def of(self, name: str) -> str | None:
        return self.by_name.get(organisation_key(name))


def organisation_key(name: str) -> str:
    return " ".join(LEGAL.sub(" ", plain(re.sub(r"^[A-Z]{2}-(?=[A-Z])", "", name.strip()))).split())


def acronym_of(name: str) -> str | None:
    match = re.search(r"\(([A-Za-z][A-Za-z0-9.\-]{1,12})\)", name)
    return plain(match.group(1)) if match else None


def resolve_organisations(
    cordis: list[tuple[str, str | None, str | None]], affiliations: list[str], same: list[tuple[str, str]]
) -> Organisations:
    names: dict[str, Counter[str]] = defaultdict(Counter)
    country: dict[str, str | None] = {}
    activity: dict[str, str | None] = {}
    official: dict[str, str] = {}
    for name, nation, kind in cordis:
        key = organisation_key(name)
        names[key][name] += 1
        official.setdefault(key, name)
        country.setdefault(key, nation)
        activity.setdefault(key, kind)
    for name in affiliations:
        key = organisation_key(name)
        if key:
            names[key][name] += 1
    union = UnionFind()
    for key in names:
        union.find(key)
    known = {f"organisation:{slug(key)}": key for key in names}
    for left, right in same:
        if left in known and right in known:
            union.union(known[left], known[right])
    groups: dict[str, list[str]] = defaultdict(list)
    for key in names:
        groups[union.find(key)].append(key)
    for root, keys in groups.items():
        for key in keys:
            if key != root:
                names[root].update(names.pop(key))
                if key in official:
                    official.setdefault(root, official[key])
                if country.get(root) is None:
                    country[root] = country.get(key)
                if activity.get(root) is None:
                    activity[root] = activity.get(key)
    result = Organisations()
    for key in sorted(names):
        name = official.get(key) or sorted(names[key].items(), key=lambda item: (-item[1], item[0]))[0][0]
        organisation_id = f"organisation:{slug(key)}"
        result.identities[organisation_id] = OrganisationIdentity(
            organisation_id=organisation_id,
            name=name,
            name_variants=tuple(sorted(names[key])),
            country=country.get(key),
            activity_type=activity.get(key),
        )
        result.by_name[key] = organisation_id
    for root, keys in groups.items():
        for key in keys:
            result.by_name[key] = result.by_name[root]
    result.candidates = candidates(result, set(official))
    return result


def candidates(organisations: Organisations, official: set[str]) -> list[tuple[str, str]]:
    acronyms: dict[str, set[str]] = defaultdict(set)
    for key, organisation_id in organisations.by_name.items():
        identity = organisations.identities[organisation_id]
        for variant in identity.name_variants:
            if acronym := acronym_of(variant):
                acronyms[acronym].add(organisation_id)
        if len(key.split()) == 1 and key.isalpha() and len(key) <= 8:
            acronyms[key].add(organisation_id)
    pairs: set[tuple[str, str]] = set()
    for members in acronyms.values():
        ordered = sorted(members)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                pairs.add((left, right))
    official_ids = {organisations.by_name[key]: key for key in official}
    for organisation_id, key in official_ids.items():
        tokens = set(key.split())
        for other_key, other_id in organisations.by_name.items():
            other_tokens = set(other_key.split())
            if other_id != organisation_id and len(other_tokens) >= 2 and other_tokens < tokens:
                pairs.add((min(organisation_id, other_id), max(organisation_id, other_id)))
    return sorted(pairs)
