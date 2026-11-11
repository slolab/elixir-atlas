import csv
import hashlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TypeVar

from biotope.graph import Evidence, SourceRecord

from ...paths import PROJECT_ROOT


Row = TypeVar("Row")


def cited(path: Path) -> tuple[str, str]:
    return path.relative_to(PROJECT_ROOT).as_posix(), "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def optional(raw: str, missing: frozenset[str]) -> str | None:
    return None if raw.strip().lower() in missing else raw


def read_csv(path: Path, record_set: str, decode: Callable[[dict[str, str]], Row]) -> Iterator[SourceRecord[Row]]:
    artifact, version = cited(path)
    with path.open(newline="", encoding="utf-8") as stream:
        number = 2
        try:
            for row in csv.DictReader(stream, strict=True):
                record = decode(row)
                yield SourceRecord(record, (Evidence(artifact, version, record_set, f"line {number}"),))
                number += 1
        except Exception as error:
            raise ValueError(f"{artifact}: line {number}: {error!r}") from error
