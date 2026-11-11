import hashlib
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, TypeVar, cast

from biotope.graph import Evidence, SourceRecord

from ...paths import PROJECT_ROOT


Row = TypeVar("Row")


def cited(path: Path) -> tuple[str, str]:
    return path.relative_to(PROJECT_ROOT).as_posix(), "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(
    path: Path, record_set: str, missing: frozenset[str], decode: Callable[[dict[str, Any]], Row]
) -> Iterator[SourceRecord[Row]]:
    artifact, version = cited(path)
    with path.open("rb") as stream:
        for number, line in enumerate(stream, start=1):
            try:
                raw = cast(dict[str, Any], json.loads(line))
                row: dict[str, Any] = {
                    key: None if isinstance(item, str) and item in missing else item for key, item in raw.items()
                }
                record = decode(row)
            except Exception as error:
                raise ValueError(f"{artifact}: line {number}: {error!r}") from error
            yield SourceRecord(record, (Evidence(artifact, version, record_set, f"line {number}"),))
