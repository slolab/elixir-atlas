import hashlib
import re
import unicodedata

TITLES = {"dr", "prof", "professor", "mr", "mrs", "ms", "phd", "md", "msc", "bsc", "sir", "dott", "ing"}
PARTICLES = {"de", "da", "das", "do", "dos", "van", "von", "der", "den", "del", "della", "di", "la", "le", "du", "ter", "ten", "y", "e"}
NOT_PEOPLE = re.compile(
    r"\b(team|group|groups|consortium|committee|board|platform|community|node|nodes|elixir|university|institute|"
    r"centre|center|hub|wp|task|partner|partners|members|leaders?|office|unit|secretariat|all|tbc|tbd|vacant|"
    r"coordinator|project|ltd|gmbh|foundation|laboratory|lab|bioinformatics|services?|network|chairs?|advisors?|"
    r"external|ethics|officers?|managers?|representatives?|staff|director|consortia|support|helpdesk|contributors|"
    r"contact|primary|forschungszentrum|universite|universitat|universidad|universita|universidade|instituto|"
    r"institut|hospital|ministry|agency|council|embl|help|helpdesk|github|projects|info|admin)\b"
)


UNDECOMPOSED = str.maketrans({"ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "ð": "d", "æ": "ae", "Æ": "AE", "œ": "oe", "ß": "ss", "þ": "th"})


def ascii_fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.translate(UNDECOMPOSED))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")


def without_emails(value: str | None) -> str | None:
    return EMAIL.sub("[email]", value) if value else value


def one_line(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.split()) or None


def list_item(value: str) -> str:
    return " ".join(value.replace(";", ",").split())


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", ascii_fold(value).lower()).strip("-") or "x"


def digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:16]


def display_name(raw: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", raw)
    if name.count(",") == 1:
        surname, given = (part.strip() for part in name.split(","))
        if surname and given:
            name = f"{given} {surname}"
    tokens = [token for token in name.replace(" ", " ").split() if token.lower().strip(".") not in TITLES]
    return " ".join(tokens)


def name_key(raw: str) -> str:
    folded = ascii_fold(display_name(raw)).lower()
    return " ".join(re.sub(r"[^a-z]+", " ", folded).split())


def is_person_name(raw: str) -> bool:
    if re.match(r"^\s*[A-Z]{2,3}-[A-Z]", raw) or not any(char.islower() for char in raw):
        return False
    key = name_key(raw)
    tokens = key.split()
    if not 2 <= len(tokens) <= 6 or any(char.isdigit() for char in raw) or "@" in raw:
        return False
    return not NOT_PEOPLE.search(key)


def core_tokens(key: str) -> list[str]:
    return [token for token in key.split() if token not in PARTICLES]


def compatible_given(left: str, right: str) -> bool:
    if left == right:
        return True
    if len(left) == 1 or len(right) == 1:
        return left[0] == right[0]
    short, long = sorted((left, right), key=len)
    return len(short) >= 3 and long.startswith(short)


def possibly_same(left: str, right: str) -> bool:
    if left == right:
        return False
    a, b = core_tokens(left), core_tokens(right)
    if len(a) < 2 or len(b) < 2:
        return False
    if a[-1] == b[-1] and compatible_given(a[0], b[0]):
        return True
    small, large = sorted((set(a), set(b)), key=len)
    return len(small) >= 2 and small < large and a[0] == b[0]
