from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import TessFacet


def _decode(row: dict[str, Any]) -> TessFacet:
    return TessFacet(
        catalogue=row["catalogue"],
        count=row["count"],
        facet=row["facet"],
        source_path=row["source_path"],
        value=row["value"],
    )


def _read(path: Path) -> Iterator[SourceRecord[TessFacet]]:
    return read_jsonl(path, TessFacet.__record_set__, TessFacet.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[TessFacet]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
