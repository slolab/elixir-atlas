from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import PlanLinkRow


def _decode(record_id: str, document: str, values: Values) -> PlanLinkRow:
    return PlanLinkRow(
        id=record_id,
        document=document,
        owner=required(values, "owner"),
        linked_project=required(values, "linked_project"),
        relation=required(values, "relation"),
        item=text(values, "item"),
        linked_item=text(values, "linked_item"),
    )


def _read(path: Path) -> Iterator[SourceRecord[PlanLinkRow]]:
    return read_records(path, PlanLinkRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[PlanLinkRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
