import re
from urllib.parse import urlsplit

from .names import ascii_fold

GROUP_KINDS = frozenset(
    {"community", "platform", "focus_group", "working_group", "task_force", "governance_group", "node_group"}
)
GROUP_WORDS = re.compile(r"\b(elixir|the|community|communities|platform|focus|group|groups)\b")
GROUP_REWRITES = (
    (re.compile(r"\brdm\b"), "research data management"),
    (re.compile(r"\bhcnv\b"), "human copy number variation"),
    (re.compile(r"\bidp\b"), "intrinsically disordered proteins"),
    (re.compile(r"\bfhd\b"), "federated human data"),
    (re.compile(r"\bml\b"), "machine learning"),
    (re.compile(r"\bmachine learning ai\b"), "machine learning"),
    (re.compile(r"\bai ecosystems\b"), "ai ecosystem"),
    (re.compile(r"\bphenome and genome\b"), "genome and phenome"),
    (re.compile(r"\bstructural bioinformatics\b"), "3d bioinfo"),
    (re.compile(r"\b3d bio ?info\b"), "3d bioinfo"),
    (re.compile(r"\bsab\b"), "scientific advisory board"),
    (re.compile(r"\biac\b"), "industry advisory committee"),
    (re.compile(r"\btecg\b"), "technical coordinators"),
    (re.compile(r"\btrcg\b"), "training coordinators"),
    (re.compile(r"\bhonc\b"), "heads of nodes committee"),
)
NAMED_KINDS = frozenset({"community", "platform"})
SITES = {
    "elixir": "elixir-europe.org",
    "node-uk": "elixiruknode.org",
    "node-norway": "elixir.no",
    "node-netherlands": "elixir.nl",
}
ZENODO_RECORD = re.compile(r"^zenodo\.org/(?:api/)?(?:records?|deposit)/(\d+)|^(?:dx\.)?doi\.org/10\.5281/zenodo\.(\d+)", re.I)
PROGRAMME_CODE = re.compile(r"(?<![0-9])(?:20)?(2[0-9])[- _](TECHNOLOGY|SCIENCE)[- _](?:commissioned services )?([A-Za-z]+)", re.I)
PROGRAMME_LABELS = frozenset({"ekes", "sepp"})
CODE_LIKE = re.compile(r"^(wp|t|d|m|task|activity)\s?\d", re.I)


def plain(value: str) -> str:
    text = ascii_fold(value).lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def family(kind: str) -> str:
    return "group" if kind in GROUP_KINDS else "project"


def is_acronym(value: str) -> bool:
    value = value.strip()
    return " " not in value and 2 <= len(value) <= 12 and sum(char.isupper() or char.isdigit() for char in value) >= 2


def without_acronyms(name: str) -> str:
    leading = re.match(r"^\s*([^\s()]{2,12})\s*\(([^)]+)\)\s*$", name)
    if leading and is_acronym(leading.group(1)) and " " in leading.group(2).strip():
        return leading.group(2)
    return re.sub(r"\(([^)]*)\)", lambda part: " " if is_acronym(part.group(1)) else f" {part.group(1)} ", name)


def group_key(name: str) -> str:
    text = plain(without_acronyms(name))
    for pattern, replacement in GROUP_REWRITES:
        text = pattern.sub(replacement, text)
    text = GROUP_WORDS.sub(" ", text)
    return " ".join(text.split())


def project_key(name: str) -> str:
    name = re.sub(r"\((?:SEP|EKES)\b[^)]*\)", " ", name, flags=re.I)
    name = re.sub(r"\(([A-Z][A-Za-z]*[A-Z])\)", " ", name)
    text = re.sub(r"\b(20\d\d) 20(\d\d)\b", r"\1 \2", plain(name))
    return re.sub(r"\s*\b(work ?plan|programme)$", "", text).strip()


def acronym_key(acronym: str | None) -> str | None:
    if not acronym:
        return None
    key = plain(acronym).replace("elixir ", "").replace(" ", "")
    if len(key) < 4 or CODE_LIKE.match(acronym.strip()) or key in PROGRAMME_LABELS:
        return None
    return key


def programme_code(*texts: str | None) -> str | None:
    for text in texts:
        if text and (match := PROGRAMME_CODE.search(text)):
            area = match.group(3).lower().removesuffix("platform")
            return f"{match.group(1)}-{match.group(2)}-{area}".lower()
    return None


def initiative_key(name: str, kind: str) -> str:
    if family(kind) == "group":
        space = kind if kind in NAMED_KINDS else "group"
        return f"{space}:{group_key(name)}"
    return f"project:{project_key(name)}"


def url_key(url: str | None, source: str | None = None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("/") and source in SITES:
        url = f"https://{SITES[source]}{url}"
    if not url.startswith("http"):
        return None
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    if record := ZENODO_RECORD.search(f"{host}{path}"):
        return f"zenodo.org/records/{record.group(1) or record.group(2)}"
    if project := re.match(r"cordis\.europa\.eu/project/id/(\d+)", f"{host}{path}"):
        return f"cordis.europa.eu/project/id/{project.group(1)}"
    return f"{host}{path}".lower()
