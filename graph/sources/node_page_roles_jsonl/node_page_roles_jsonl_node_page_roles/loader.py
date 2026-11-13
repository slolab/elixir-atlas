from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import NodePageRoleRow


def _decode(record_id: str, document: str, values: Values) -> NodePageRoleRow:
    return NodePageRoleRow(
        id=record_id,
        document=document,
        person_name=required(values, "person"),
        role=required(values, "role"),
        role_kind=required(values, "role_kind"),
        place=required(values, "place"),
        place_kind=required(values, "place_kind"),
        affiliation=text(values, "affiliation"),
        node=text(values, "node"),
        orcid=text(values, "orcid"),
    )


def _read(path: Path) -> Iterator[SourceRecord[NodePageRoleRow]]:
    return read_records(path, NodePageRoleRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[NodePageRoleRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
