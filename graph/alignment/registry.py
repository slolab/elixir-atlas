import re
from collections.abc import Callable
from dataclasses import dataclass

from .initiatives import Claim
from .keys import GROUP_REWRITES, plain, url_key, without_acronyms
from .names import slug

KIND_ORDER = ("community", "platform", "focus_group")
QUALIFIERS = {"community": "communit(?:y|ies)", "platform": "platforms?", "focus_group": "focus groups?"}
LABELS = {"community": "Community", "platform": "Platform", "focus_group": "Focus Group"}
PLURAL = re.compile(r"\b(Communities|Platforms|Focus Groups)\b", re.I)
ENUMERATION_STOP = re.compile(r"[.;:()\n]|\b(?:communit\w*|platforms?|focus groups?|as well as)\b", re.I)
CONJUNCTION = re.compile(r"\s(?:and|&)\s")
LIST_SPLIT = re.compile(r",\s*(?:and\s+|&\s+)?|\s+(?:and|&)\s+")
SINGULAR = {"communities": "Community", "platforms": "Platform", "focus groups": "Focus Group"}


@dataclass(frozen=True)
class Entry:
    claim_id: str
    name: str
    kind: str
    status: str
    url: str
    start: str | None
    end: str | None
    became: str | None
    became_date: str | None
    document: str


def full_name(name: str, kind: str) -> str:
    label = LABELS[kind]
    return name if plain(name).endswith(plain(label)) else f"{name} {label}"


def bare(name: str, kind: str) -> str:
    text = plain(name)
    return text.removesuffix(plain(LABELS[kind])).strip()


def normalised(text: str) -> str:
    text = plain(without_acronyms(text))
    for pattern, replacement in GROUP_REWRITES:
        text = pattern.sub(replacement, text)
    return text


def priority(entry: Entry) -> tuple[bool, int, str]:
    return entry.status != "current", KIND_ORDER.index(entry.kind), entry.claim_id


def registry_claims(entries: list[Entry], page_key: Callable[[str | None], str | None]) -> list[Claim]:
    taken: set[str] = set()
    claims: list[Claim] = []
    for entry in sorted(entries, key=priority):
        key = page_key(entry.url)
        own = key is not None and key not in taken
        if key:
            taken.add(key)
        claims.append(Claim(entry.claim_id, entry.name, None, entry.kind, "described" if own else "listed", entry.url if own else None, ()))
    return claims


def entry_id(name: str, kind: str) -> str:
    return f"registry:{kind}:{slug(bare(name, kind))}"


class Phrases:
    def __init__(self, entries: list[Entry], initiative_of: dict[str, str]) -> None:
        self.patterns: list[tuple[re.Pattern[str], str]] = []
        for entry in sorted(entries, key=priority):
            words = normalised(bare(entry.name, entry.kind)).split() or [""]
            last = words[-1]
            variants = {last, last.removesuffix("s") if last.endswith("s") else f"{last}s"}
            head = " ".join(words[:-1])
            phrase = "|".join(sorted(re.escape(f"{head} {v}".strip()) for v in variants))
            prefix = r"elixir (?:s )?" if entry.kind == "platform" else ""
            pattern = re.compile(rf"\b{prefix}(?:{phrase}) {QUALIFIERS[entry.kind]}\b")
            if last and entry.claim_id in initiative_of:
                self.patterns.append((pattern, initiative_of[entry.claim_id]))

    def find(self, text: str | None) -> list[str]:
        if not text:
            return []
        found = normalised(spread(text))
        return list(dict.fromkeys(initiative_id for pattern, initiative_id in self.patterns if pattern.search(found)))

    def one(self, text: str | None) -> str | None:
        found = self.find(text)
        return found[0] if len(found) == 1 else None


def spread(text: str) -> str:
    pieces: list[str] = []
    done = 0
    for match in PLURAL.finditer(text):
        window = text[max(done, match.start() - 300) : match.start()]
        stops = list(ENUMERATION_STOP.finditer(window))
        segment = window[stops[-1].end() if stops else 0 :]
        parts = [part.strip() for part in LIST_SPLIT.split(segment) if part.strip()]
        if not CONJUNCTION.search(segment) or len(parts) < 2 or any(len(part) > 60 for part in parts[1:]):
            continue
        label = SINGULAR[" ".join(match.group(1).lower().split())]
        prefix = "ELIXIR " if label == "Platform" and "elixir" in segment.lower() else ""
        named = ", ".join(f"{prefix if not part.lower().startswith('elixir') else ''}{part[-60:]} {label}" for part in parts)
        pieces += [text[done : match.start() - len(segment)], " " if segment[:1].isspace() else "", named]
        done = match.end()
    return "".join([*pieces, text[done:]])


def page_url_key(url: str | None, redirects: dict[str, str]) -> str | None:
    key = url_key(url)
    return redirects.get(key, key) if key else None
