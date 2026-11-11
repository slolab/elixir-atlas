from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import RoleStatementRow


def _decode(record_id: str, document: str, values: Values) -> RoleStatementRow:
    return RoleStatementRow(
        id=record_id,
        document=document,
        person_name=required(values, "person"),
        role=required(values, "role"),
        role_kind=required(values, "role_kind"),
        place=required(values, "place"),
        place_kind=required(values, "place_kind"),
        work_item=text(values, "work_item"),
        affiliation=text(values, "affiliation"),
        node=text(values, "node"),
        period=text(values, "period"),
        effort=text(values, "effort"),
        funding=required(values, "funding"),
        email=text(values, "email"),
    )


def _read(path: Path) -> Iterator[SourceRecord[RoleStatementRow]]:
    return read_records(path, RoleStatementRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[RoleStatementRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
