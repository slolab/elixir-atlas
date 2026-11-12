from collections.abc import Iterator
from pathlib import Path
from typing import cast

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import ElectionCandidateRow


def _decode(record_id: str, document: str, values: Values) -> ElectionCandidateRow:
    return ElectionCandidateRow(
        id=record_id,
        document=document,
        community=required(values, "community"),
        person=required(values, "person"),
        country=text(values, "country"),
        affiliation=text(values, "affiliation"),
        note=text(values, "note"),
        year=int(cast(int, values["year"])),
    )


def _read(path: Path) -> Iterator[SourceRecord[ElectionCandidateRow]]:
    return read_records(path, ElectionCandidateRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[ElectionCandidateRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
