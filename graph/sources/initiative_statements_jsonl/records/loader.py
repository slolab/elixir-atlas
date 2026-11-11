from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, strings, text
from . import SOURCE
from .schema import InitiativeStatementRow


def _decode(record_id: str, document: str, values: Values) -> InitiativeStatementRow:
    return InitiativeStatementRow(
        id=record_id,
        document=document,
        name=required(values, "name"),
        acronym=text(values, "acronym"),
        kind=required(values, "kind"),
        coverage=required(values, "coverage"),
        status=required(values, "status"),
        period=text(values, "period"),
        start=text(values, "start"),
        end=text(values, "end"),
        summary=text(values, "summary"),
        outcomes=strings(values, "outcomes"),
        nodes=strings(values, "nodes"),
        leads=strings(values, "leads"),
        related=strings(values, "related"),
        topics=strings(values, "topics"),
        contacts=strings(values, "contacts"),
        links=strings(values, "links"),
        funding=text(values, "funding"),
    )


def _read(path: Path) -> Iterator[SourceRecord[InitiativeStatementRow]]:
    return read_records(path, InitiativeStatementRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[InitiativeStatementRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
