import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.extraction import EXTRACTIONS
from graph.extraction._reading import document_text, person_links, squashed
from graph.extraction.roles import names_match, unmatched
from graph.paths import PROJECT_ROOT

FIXTURES = PROJECT_ROOT / "eval/extraction/fixtures.yaml"


def records(name: str, revision: str | None = None) -> dict[str, list[dict[str, object]]]:
    by_document: dict[str, list[dict[str, object]]] = defaultdict(list)
    path = f"data/extracted/{name}.jsonl"
    if revision:
        lines = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.splitlines()
    elif (PROJECT_ROOT / path).is_file():
        lines = (PROJECT_ROOT / path).read_text(encoding="utf-8").splitlines()
    else:
        lines = []
    for line in lines:
        raw = json.loads(line)
        values = raw["values"]
        by_document[raw["document"]].append(
            {key: [item["value"] for item in field] if isinstance(field, list) else field["value"] for key, field in values.items()}
        )
    return by_document


def matches(record: dict[str, object], wanted: dict[str, object]) -> bool:
    for key, expected in wanted.items():
        actual = record.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif isinstance(actual, list):
            if not any(squashed(str(expected)) in squashed(str(item)) for item in actual):
                return False
        elif squashed(str(expected)) not in squashed(str(actual or "")):
            return False
    return True


def fixtures() -> int:
    failures = 0
    cache: dict[str, dict[str, list[dict[str, object]]]] = {}
    for fixture in yaml.safe_load(FIXTURES.read_text(encoding="utf-8")):
        extraction = fixture["extraction"]
        by_document = cache.setdefault(extraction, records(extraction))
        paths = {path.relative_to(PROJECT_ROOT).as_posix() for path in PROJECT_ROOT.glob(fixture["documents"])}
        found = [record for path in paths for record in by_document.get(path, [])]
        for wanted in fixture.get("expect", []):
            ok = any(matches(record, wanted) for record in found)
            failures += not ok
            print(f"{'pass' if ok else 'FAIL'}  expect  {fixture['documents']}  {wanted}")
        for wanted in fixture.get("forbid", []):
            ok = not any(matches(record, wanted) for record in found)
            failures += not ok
            print(f"{'pass' if ok else 'FAIL'}  forbid  {fixture['documents']}  {wanted}")
    return failures


def coverage() -> None:
    roles = records("role_statements")
    extraction = next(item for item in EXTRACTIONS if item.name == "role_statements")
    paths = sorted({path for pattern in extraction.files for path in PROJECT_ROOT.glob(pattern) if path.suffix == ".html"})
    documents = linked = lost = missed = empty = 0
    worst: list[tuple[int, str, list[str]]] = []
    for path in paths:
        names = person_links(path)
        if not names:
            continue
        documents += 1
        document = path.relative_to(PROJECT_ROOT).as_posix()
        text = squashed(document_text(path))
        kept = [name for name in names if squashed(name) in text]
        missing = unmatched(kept, [{"person": {"value": record["person"]}} for record in roles.get(document, [])])
        linked += len(names)
        lost += len(names) - len(kept)
        missed += len(missing)
        empty += not roles.get(document)
        if missing:
            worst.append((len(missing), document, missing))
    print(f"\nrole documents linking people: {documents}")
    print(f"linked people: {linked}; lost in cleaning: {lost}; no record: {missed}; documents with no records: {empty}")
    for count, document, missing in sorted(worst, reverse=True)[:15]:
        print(f"  {count:3}  {document}  {'; '.join(missing[:6])}")


def regressions(revision: str = "HEAD") -> None:
    before, after = records("role_statements", revision), records("role_statements")
    dropped = []
    for document, old in before.items():
        if document not in after:
            continue
        people = [str(record["person"]) for record in after[document]]
        lost = sorted({str(record["person"]) for record in old} - {person for person in people})
        lost = [name for name in lost if not any(names_match(name, person) for person in people)]
        if lost:
            dropped.append((len(lost), document, lost))
    print(f"\npeople dropped since {revision}, in documents still extracted: {sum(count for count, _, _ in dropped)} in {len(dropped)} documents")
    for count, document, lost in sorted(dropped, reverse=True)[:15]:
        print(f"  {count:3}  {document}  {'; '.join(lost[:6])}")


if __name__ == "__main__":
    failed = fixtures()
    coverage()
    regressions()
    sys.exit(1 if failed else 0)
