from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import GroupDirectoryRow


def _decode(record_id: str, document: str, values: Values) -> GroupDirectoryRow:
    return GroupDirectoryRow(
        id=record_id,
        document=document,
        name=required(values, "name"),
        kind=required(values, "kind"),
        status=required(values, "status"),
        url=required(values, "url"),
        start=text(values, "start"),
        end=text(values, "end"),
        became=text(values, "became"),
        became_date=text(values, "became_date"),
    )


def _read(path: Path) -> Iterator[SourceRecord[GroupDirectoryRow]]:
    return read_records(path, GroupDirectoryRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[GroupDirectoryRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
