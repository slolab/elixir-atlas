from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, strings, text
from . import SOURCE
from .schema import ElixirPageRow


def _decode(record_id: str, document: str, values: Values) -> ElixirPageRow:
    return ElixirPageRow(
        id=record_id,
        document=document,
        published=text(values, "published"),
        modified=text(values, "modified"),
        contacts=strings(values, "contacts"),
        contact_targets=strings(values, "contact_targets"),
        join_url=text(values, "join_url"),
        joining=text(values, "joining"),
    )


def _read(path: Path) -> Iterator[SourceRecord[ElixirPageRow]]:
    return read_records(path, ElixirPageRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[ElixirPageRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
