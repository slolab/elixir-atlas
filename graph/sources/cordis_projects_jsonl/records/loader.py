from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, number, required, text
from . import SOURCE
from .schema import CordisProjectRow


def _decode(record_id: str, document: str, values: Values) -> CordisProjectRow:
    return CordisProjectRow(
        id=record_id,
        document=document,
        grant_id=required(values, "grant_id"),
        acronym=required(values, "acronym"),
        title=text(values, "title"),
        start=text(values, "start"),
        end=text(values, "end"),
        total_cost_eur=number(values, "total_cost_eur"),
        eu_contribution_eur=number(values, "eu_contribution_eur"),
        coordinator=text(values, "coordinator"),
        objective=text(values, "objective"),
    )


def _read(path: Path) -> Iterator[SourceRecord[CordisProjectRow]]:
    return read_records(path, CordisProjectRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[CordisProjectRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
