from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import BiotoolsDomain


def _decode(row: dict[str, Any]) -> BiotoolsDomain:
    return BiotoolsDomain(biotools_id=row["biotools_id"], domain=row["domain"], source_path=row["source_path"])


def _read(path: Path) -> Iterator[SourceRecord[BiotoolsDomain]]:
    return read_jsonl(path, BiotoolsDomain.__record_set__, BiotoolsDomain.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[BiotoolsDomain]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
