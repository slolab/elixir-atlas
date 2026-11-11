from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import F1000Item


def _decode(row: dict[str, Any]) -> F1000Item:
    return F1000Item(
        person_names=row["creator_names"],
        date=row.get("date"),
        description=row.get("description"),
        doi=row.get("doi"),
        item_path=row["item_path"],
        kind=row["kind"],
        source_path=row["source_path"],
        subjects=row["subjects"],
        title=row.get("title"),
    )


def _read(path: Path) -> Iterator[SourceRecord[F1000Item]]:
    return read_jsonl(path, F1000Item.__record_set__, F1000Item.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[F1000Item]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
