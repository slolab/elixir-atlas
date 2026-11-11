from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, number, required, text
from . import SOURCE
from .schema import CordisParticipantRow


def _decode(record_id: str, document: str, values: Values) -> CordisParticipantRow:
    return CordisParticipantRow(
        id=record_id,
        document=document,
        grant_id=required(values, "grant_id"),
        organisation=required(values, "organisation"),
        country=text(values, "country"),
        participation=required(values, "participation"),
        participation_ended=values.get("participation_ended") is True,
        net_eu_contribution_eur=number(values, "net_eu_contribution_eur"),
        total_cost_eur=number(values, "total_cost_eur"),
        activity_type=text(values, "activity_type"),
    )


def _read(path: Path) -> Iterator[SourceRecord[CordisParticipantRow]]:
    return read_records(path, CordisParticipantRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[CordisParticipantRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
