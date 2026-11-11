import hashlib
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypeVar, cast

from biotope.graph import Evidence, SourceRecord

from ..paths import PROJECT_ROOT

Row = TypeVar("Row")
Values = dict[str, object]


def read_records(path: Path, record_set: str, decode: Callable[[str, str, Values], Row]) -> Iterator[SourceRecord[Row]]:
    artifact = path.relative_to(PROJECT_ROOT).as_posix()
    version = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open("rb") as stream:
        for number, line in enumerate(stream, start=1):
            try:
                raw = cast(dict[str, object], json.loads(line))
                fields = cast(dict[str, object], raw["values"])
                values = {name: value_of(field) for name, field in fields.items()}
                record = decode(cast(str, raw["id"]), cast(str, raw["document"]), values)
                provenance = cast(dict[str, object], raw["provenance"])
                cited = Evidence(
                    cast(str, raw["document"]),
                    f"sha256:{provenance['document_sha256']}",
                    record_set,
                    located(fields),
                )
            except Exception as error:
                raise ValueError(f"{artifact}: line {number}: {error!r}") from error
            yield SourceRecord(record, (Evidence(artifact, version, record_set, f"line {number}"), cited))


def value_of(field: object) -> object:
    if isinstance(field, list):
        return [value_of(item) for item in cast(list[object], field)]
    return cast(dict[str, object], field).get("value")


def located(fields: dict[str, object]) -> str:
    for field in fields.values():
        if not isinstance(field, dict):
            continue
        evidence = cast(dict[str, object], cast(dict[str, object], field).get("evidence") or {})
        quote = evidence.get("quote")
        locator = evidence.get("locator")
        if quote or locator:
            parts = [str(part) for part in (locator, quote) if part]
            return ": ".join(parts)
    return "record"


def text(values: Values, name: str) -> str | None:
    value = values.get(name)
    return value if isinstance(value, str) and value else None


def required(values: Values, name: str) -> str:
    value = text(values, name)
    if value is None:
        raise ValueError(f"missing {name}")
    return value


def strings(values: Values, name: str) -> list[str]:
    return [item for item in cast(list[object], values.get(name) or []) if isinstance(item, str) and item]


def number(values: Values, name: str) -> float | None:
    value = values.get(name)
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None
