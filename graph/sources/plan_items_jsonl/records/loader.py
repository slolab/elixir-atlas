from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, strings, text
from . import SOURCE
from .schema import PlanItemRow


def _decode(record_id: str, document: str, values: Values) -> PlanItemRow:
    return PlanItemRow(
        id=record_id,
        document=document,
        owner=required(values, "owner"),
        kind=required(values, "kind"),
        code=text(values, "code"),
        label=required(values, "label"),
        description=text(values, "description"),
        parent=text(values, "parent"),
        date=text(values, "date"),
        date_as_written=text(values, "date_as_written"),
        status=required(values, "status"),
        leads=strings(values, "leads"),
        participants=strings(values, "participants"),
        effort=text(values, "effort"),
        link=text(values, "link"),
        topics=strings(values, "topics"),
    )


def _read(path: Path) -> Iterator[SourceRecord[PlanItemRow]]:
    return read_records(path, PlanItemRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[PlanItemRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
