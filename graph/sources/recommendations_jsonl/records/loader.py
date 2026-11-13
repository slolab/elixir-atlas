from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from ..._extracted import Values, read_records, required, text
from . import SOURCE
from .schema import RecommendationRow


def _decode(record_id: str, document: str, values: Values) -> RecommendationRow:
    return RecommendationRow(
        id=record_id,
        document=document,
        resource=required(values, "resource"),
        kind=required(values, "kind"),
        group=required(values, "group"),
        basis=required(values, "basis"),
        purpose=text(values, "purpose"),
        url=text(values, "url"),
    )


def _read(path: Path) -> Iterator[SourceRecord[RecommendationRow]]:
    return read_records(path, RecommendationRow.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[RecommendationRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
