import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .keys import GROUP_KINDS, acronym_key, family, initiative_key, plain, programme_code, url_key
from .names import slug
from .people import UnionFind

PLATFORM_SERVICES = (("compute", "24-compute"), ("data", "data"), ("interoperability", "interoperability"), ("tools", "tools"), ("training", "training"))
CURATED_ALIASES: tuple[tuple[str, str, str], ...] = (
    *(
        (
            f"elixir-europe.org/internal-projects/commissioned-services/2024-{platform}",
            f"elixir-europe.org/how-we-work/scientific-programme/technology/{page}",
            f"Both pages describe the {platform.title()} Platform's 2024-26 Commissioned Service "
            f"(2024-TECHNOLOGY-{platform.title()}): same platform, period and work programme; the list pages link both.",
        )
        for platform, page in PLATFORM_SERVICES
    ),
    *(
        (
            f"elixir-europe.org/{left}",
            f"elixir-europe.org/{right}",
            "Two ELIXIR website URLs of the same Scientific Programme area page: same name and summary.",
        )
        for left, right in (
            ("internal-projects/commissioned-services/science/cmr", "internal-projects/commissioned-services/science/cellular-molecular-research"),
            ("how-we-work/scientific-programme/science/hdtr", "internal-projects/commissioned-services/science/human-data-translational-research"),
            ("how-we-work/scientific-programme/science/bfsp", "internal-projects/commissioned-services/science/biodiversity-security-pathogens"),
        )
    ),
    (
        "zenodo.org/records/19469586",
        "elixir-europe.org/how-we-work/scientific-programme/science/bfsp",
        "The Zenodo record is the 2024-2028 work plan of the Biodiversity, Food Security and Pathogens programme "
        "(24-SCIENCE-BFSP) that the programme page describes.",
    ),
)


GENERIC_WORDS = frozenset({"elixir", "platform", "community", "group", "working", "focus", "project", "the", "and", "of", "for", "in"})


def words(name: str) -> set[str]:
    return set(plain(name).split()) - GENERIC_WORDS


BRACKETED_ACRONYM = re.compile(r"\(([A-Z][A-Za-z]*[A-Z])\)")
WORK_PACKAGE = re.compile(r"\b(WP|Work ?Package)\s?\d+", re.I)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    name: str
    acronym: str | None
    kind: str
    coverage: str
    url: str | None
    links: tuple[str, ...]


@dataclass(frozen=True)
class InitiativeIdentity:
    initiative_id: str
    name: str
    acronym: str | None
    kind: str
    family: str
    aliases: tuple[str, ...]
    pages: tuple[str, ...]
    identity_basis: tuple[str, ...]
    claims: tuple[str, ...]


@dataclass
class Initiatives:
    by_claim: dict[str, str] = field(default_factory=dict[str, str])
    identities: dict[str, InitiativeIdentity] = field(default_factory=dict[str, InitiativeIdentity])
    by_key: dict[str, str] = field(default_factory=dict[str, str])
    by_acronym: dict[str, str] = field(default_factory=dict[str, str])
    by_url: dict[str, str] = field(default_factory=dict[str, str])
    candidates: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])

    def resolve(self, name: str, kind: str | None = None) -> str | None:
        groups = ["community", "platform", "focus_group", "working_group", "task_force", "governance_group"]
        kinds = ["other_project", *groups] if kind and kind not in GROUP_KINDS else [*([kind] if kind else []), *groups, "other_project"]
        for candidate in kinds:
            if found := self.by_key.get(initiative_key(name, candidate)):
                return found
        acronym = acronym_key(name)
        return self.by_acronym.get(acronym) if acronym else None


def segment(page: str) -> str:
    return page.rstrip("/").rsplit("/", 1)[-1]


def is_document(page: str) -> bool:
    return page.startswith(("zenodo.org/records/", "f1000research.com/")) or page.endswith(".pdf")


def clash(left: set[str], right: set[str]) -> bool:
    return any(
        a.split("/", 1)[0] == b.split("/", 1)[0] and segment(a) != segment(b)
        for a in left
        for b in right
        if not is_document(a) and not is_document(b)
    )


class Clusters:
    def __init__(self) -> None:
        self.union = UnionFind()
        self.pages: dict[str, set[str]] = defaultdict(set)
        self.registry: dict[str, set[str]] = defaultdict(set)

    def join(self, left: str, right: str, guarded: bool = True) -> bool:
        a, b = self.union.find(left), self.union.find(right)
        if a == b:
            return True
        if self.registry[a] and self.registry[b]:
            return False
        if guarded and clash(self.pages[a], self.pages[b]):
            return False
        self.union.union(a, b)
        root = self.union.find(a)
        self.pages[root] = self.pages.pop(a, set()) | self.pages.pop(b, set()) | self.pages[root]
        self.registry[root] = self.registry.pop(a, set()) | self.registry.pop(b, set()) | self.registry[root]
        return True


def head(name: str) -> str | None:
    part = name.split(":", 1)[0].strip()
    return part if ":" in name and part else None


def resolve_initiatives(claims: list[Claim], redirects: dict[str, str], same: list[tuple[str, str]]) -> Initiatives:
    clusters_ = Clusters()
    union = clusters_.union
    reasons: list[tuple[str, str]] = []
    own_url: dict[str, str] = {}

    def page_key(url: str | None) -> str | None:
        key = url_key(url)
        return redirects.get(key, key) if key else None

    for claim in claims:
        union.find(claim.claim_id)
        if claim.claim_id.startswith("registry:"):
            clusters_.registry[claim.claim_id].add(claim.claim_id)
        key = page_key(claim.url)
        if claim.coverage == "described" and key:
            own_url[claim.claim_id] = key
            clusters_.pages[f"url:{key}"].add(key)
            clusters_.join(claim.claim_id, f"url:{key}", guarded=False)
            reasons.append((claim.claim_id, "page"))
    for left, right, _ in CURATED_ALIASES:
        clusters_.join(f"url:{left}", f"url:{right}", guarded=False)
        reasons.append((f"url:{left}", "curated_alias"))
    for claim in claims:
        own = claim.url if claim.coverage == "described" else None
        if family(claim.kind) == "project" and (code := programme_code(claim.name, claim.acronym, own)):
            if clusters_.join(claim.claim_id, f"programme:{code}"):
                reasons.append((claim.claim_id, "programme_code"))
    pages = set(own_url.values())
    for claim in claims:
        own = own_url.get(claim.claim_id)
        if own and family(claim.kind) == "project" and (WORK_PACKAGE.search(claim.name) or "/eu-projects/" in own):
            parents = sorted((page for page in pages if own.startswith(f"{page}/")), key=len)
            if parents and clusters_.join(claim.claim_id, f"url:{parents[-1]}", guarded=False):
                reasons.append((claim.claim_id, "sub_page"))
    documents = {key for key in pages if is_document(key)}
    linking: dict[str, set[str]] = defaultdict(set)
    for claim in claims:
        if claim.coverage == "described" and family(claim.kind) == "project" and claim.claim_id in own_url:
            for link in claim.links:
                key = page_key(link)
                if key in documents and key != own_url[claim.claim_id]:
                    linking[key].add(own_url[claim.claim_id])
    for document, linked in sorted(linking.items()):
        if len(linked) == 1 and clusters_.join(f"url:{document}", f"url:{next(iter(linked))}"):
            reasons.append((f"url:{document}", "work_plan_link"))
    families: dict[str, set[str]] = defaultdict(set)
    named: dict[str, set[str]] = defaultdict(set)
    for claim in claims:
        if claim.claim_id in own_url:
            families[own_url[claim.claim_id]].add(family(claim.kind))
            named[own_url[claim.claim_id]] |= words(claim.name) | words(claim.acronym or "")
    for claim in claims:
        for link in claim.links:
            key = page_key(link)
            if (
                key in pages
                and claim.coverage == "listed"
                and family(claim.kind) in families[key]
                and words(f"{claim.name} {claim.acronym or ''}") & named[key]
            ):
                if clusters_.join(claim.claim_id, f"url:{key}"):
                    reasons.append((claim.claim_id, "link"))
    for claim in claims:
        clusters_.join(claim.claim_id, f"key:{initiative_key(claim.name, claim.kind)}")
        if family(claim.kind) != "project":
            continue
        if (part := head(claim.name)) is not None:
            clusters_.join(claim.claim_id, f"key:{initiative_key(part, claim.kind)}")
        bracketed = BRACKETED_ACRONYM.search(claim.name)
        for value in (claim.acronym, claim.name if " " not in claim.name.strip() else None, bracketed.group(1) if bracketed else None):
            if acronym := acronym_key(value):
                clusters_.join(claim.claim_id, f"acronym:{acronym}")
    for left, right in same:
        clusters_.join(left, right, guarded=False)
        reasons.append((left, "decision"))
    basis: dict[str, set[str]] = defaultdict(set)
    for node, reason in reasons:
        basis[union.find(node)].add(reason)
    clusters: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        clusters[union.find(claim.claim_id)].append(claim)
    result = Initiatives()
    taken: set[str] = set()
    for root in sorted(clusters, key=lambda r: sorted(c.claim_id for c in clusters[r])[0]):
        group = clusters[root]
        described = [c for c in group if c.coverage == "described"]
        by_length = sorted({own_url[c.claim_id] for c in described if c.claim_id in own_url}, key=lambda u: (not u.startswith("elixir-europe.org"), len(u), u))
        own = sorted(by_length, key=lambda u: (not u.startswith("elixir-europe.org"), u.startswith("elixir-europe.org/internal-projects/")))
        primary = [c for c in described if c.claim_id in own_url and own_url[c.claim_id] == own[0]] if own else []
        kinds = Counter(c.kind for c in primary or described or group)
        kind = sorted(kinds.items(), key=lambda item: (-item[1], item[0]))[0][0]
        names = Counter(c.name for c in group)
        listed = [c for c in group if c.claim_id.startswith("registry:")] or primary
        name = listed[0].name if listed else sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        acronyms = Counter(c.acronym for c in group if c.acronym and family(c.kind) == "project")
        acronym = sorted(acronyms.items(), key=lambda item: (-item[1], item[0]))[0][0] if acronyms and family(kind) == "project" else None
        paths = [page.split("/", 1)[1] for page in by_length if "/" in page and page not in documents]
        names_tried = [*(slug(segment(path)) for path in paths), slug(paths[0])] if paths else [slug(plain(name))]
        initiative_id = next((f"initiative:{n}" for n in names_tried if f"initiative:{n}" not in taken), None)
        counter = 2
        while initiative_id is None:
            candidate = f"initiative:{names_tried[-1]}-{counter}"
            initiative_id = candidate if candidate not in taken else None
            counter += 1
        taken.add(initiative_id)
        why = set(basis.get(root, set()))
        keys = Counter(initiative_key(c.name, c.kind) for c in group)
        if any(count > 1 for count in keys.values()):
            why.add("same_name")
        acronyms_seen = Counter(acronym_key(c.acronym) for c in group if c.acronym and family(c.kind) == "project")
        if any(count > 1 and value for value, count in acronyms_seen.items()):
            why.add("acronym")
        result.identities[initiative_id] = InitiativeIdentity(
            initiative_id=initiative_id,
            name=name,
            acronym=acronym,
            kind=kind,
            family=family(kind),
            aliases=tuple(sorted(names)),
            pages=tuple(f"https://{page}" for page in own),
            identity_basis=tuple(sorted(why or {"single_source"})),
            claims=tuple(sorted(c.claim_id for c in group)),
        )
        for claim in group:
            result.by_claim[claim.claim_id] = initiative_id
            result.by_key.setdefault(initiative_key(claim.name, claim.kind), initiative_id)
            if family(claim.kind) == "project" and (acronym_value := acronym_key(claim.acronym)):
                result.by_acronym.setdefault(acronym_value, initiative_id)
        for page in own:
            result.by_url[page] = initiative_id
    result.candidates = candidates(result)
    return result


def candidates(initiatives: Initiatives) -> list[tuple[str, str]]:
    entries: list[tuple[str, frozenset[str], str]] = []
    codes = {
        identity.initiative_id: {code for alias in identity.aliases if (code := programme_code(alias))}
        for identity in initiatives.identities.values()
    }
    for identity in initiatives.identities.values():
        for alias in identity.aliases:
            tokens = frozenset(plain(alias).replace("elixir", " ").split())
            if len(tokens) >= 2:
                entries.append((identity.family, tokens, identity.initiative_id))
    by_token: dict[str, list[int]] = defaultdict(list)
    for index, (_, tokens, _) in enumerate(entries):
        for token in tokens:
            by_token[token].append(index)
    pairs: set[tuple[str, str]] = set()
    for index, (group, tokens, left) in enumerate(entries):
        seen: set[int] = set()
        for token in tokens:
            if len(by_token[token]) > 60:
                continue
            for other in by_token[token]:
                if other <= index or other in seen:
                    continue
                seen.add(other)
                other_group, other_tokens, right = entries[other]
                if right == left or other_group != group or (codes[left] and codes[right] and not codes[left] & codes[right]):
                    continue
                overlap = len(tokens & other_tokens) / len(tokens | other_tokens)
                if overlap >= 0.75 or (min(len(tokens), len(other_tokens)) >= 3 and (tokens < other_tokens or other_tokens < tokens)):
                    pairs.add((min(left, right), max(left, right)))
    return sorted(pairs)
