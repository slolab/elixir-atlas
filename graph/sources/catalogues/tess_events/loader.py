from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import TessEvent


def _decode(row: dict[str, Any]) -> TessEvent:
    return TessEvent(
        city=row.get("city"),
        collection_ids=row["collection_ids"],
        content_provider_id=row.get("content_provider_id"),
        country=row.get("country"),
        description=row.get("description"),
        end=row.get("end"),
        event_types=row["event_types"],
        host_institutions=row["host_institutions"],
        keywords=row["keywords"],
        node_ids=row["node_ids"],
        online=row.get("online"),
        organizer=row.get("organizer"),
        source_path=row["source_path"],
        start=row.get("start"),
        tess_id=row["tess_id"],
        title=row.get("title"),
        topic_labels=row["topic_labels"],
        edam_topic_uris=row["topic_uris"],
        url=row.get("url"),
    )


def _read(path: Path) -> Iterator[SourceRecord[TessEvent]]:
    return read_jsonl(path, TessEvent.__record_set__, TessEvent.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[TessEvent]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
