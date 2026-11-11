import re
from collections import Counter, defaultdict

ZENODO_ID = re.compile(r"zenodo\.org/(?:records?|deposit|uploads)/(\d+)|zenodo\.(\d+)", re.I)


def names_by_count(facets: list[tuple[str, str, int]], ids: dict[str, Counter[str]]) -> dict[str, str]:
    found: dict[str, set[str]] = defaultdict(set)
    for catalogue, counter in ids.items():
        by_count: dict[int, list[str]] = defaultdict(list)
        for identifier, count in counter.items():
            by_count[count].append(identifier)
        values: dict[int, list[str]] = defaultdict(list)
        for facet_catalogue, value, count in facets:
            if facet_catalogue == catalogue:
                values[count].append(value)
        for count, names in values.items():
            if len(names) == 1 and len(by_count.get(count, [])) == 1:
                found[by_count[count][0]].add(names[0])
    named = {identifier: next(iter(names)) for identifier, names in found.items() if len(names) == 1}
    clashes = Counter(named.values())
    return {identifier: name for identifier, name in named.items() if clashes[name] == 1}


def zenodo_record_id(value: str | None) -> str | None:
    if not value:
        return None
    match = ZENODO_ID.search(value)
    return (match.group(1) or match.group(2)) if match else None


def collection_name(title: str) -> str:
    return re.split(r"[:(]| - ", title, maxsplit=1)[0].strip()
