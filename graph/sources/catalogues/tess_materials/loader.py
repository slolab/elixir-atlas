from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import TessMaterial


def _decode(row: dict[str, Any]) -> TessMaterial:
    return TessMaterial(
        authors=row["authors"],
        collection_ids=row["collection_ids"],
        content_provider_id=row.get("content_provider_id"),
        date_published=row.get("date_published"),
        description=row.get("description"),
        doi=row.get("doi"),
        keywords=row["keywords"],
        node_ids=row["node_ids"],
        resource_types=row["resource_types"],
        source_path=row["source_path"],
        tess_id=row["tess_id"],
        title=row.get("title"),
        topic_labels=row["topic_labels"],
        edam_topic_uris=row["topic_uris"],
        url=row.get("url"),
    )


def _read(path: Path) -> Iterator[SourceRecord[TessMaterial]]:
    return read_jsonl(path, TessMaterial.__record_set__, TessMaterial.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[TessMaterial]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
