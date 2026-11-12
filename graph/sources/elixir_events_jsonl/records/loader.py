from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import ElixirEventRow


def _decode(record_id: str, document: str, values: Values) -> ElixirEventRow:
    return ElixirEventRow(
        id=record_id,
        document=document,
        title=required(values, "title"),
        start=text(values, "start"),
        end=text(values, "end"),
        url=text(values, "url"),
    )


def _read(path: Path) -> Iterator[SourceRecord[ElixirEventRow]]:
    return read_records(path, ElixirEventRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[ElixirEventRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
