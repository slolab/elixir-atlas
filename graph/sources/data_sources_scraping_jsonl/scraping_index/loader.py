from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import ScrapingIndexRow


def _decode(row: dict[str, Any]) -> ScrapingIndexRow:
    return ScrapingIndexRow(
        bytes=row.get("bytes"),
        content_type=row.get("content_type"),
        discovered_from=row.get("discovered_from"),
        discovery_status=row.get("discovery_status"),
        error=row.get("error"),
        final_url=row.get("final_url"),
        links=row.get("links"),
        note=row.get("note"),
        path=row.get("path"),
        previous_path=row.get("previous_path"),
        reason=row.get("reason"),
        representation=row.get("representation"),
        retrieved_at=row.get("retrieved_at"),
        reviewed_at=row.get("reviewed_at"),
        source=row["source"],
        status=row["status"],
        updated_at=row.get("updated_at"),
        url=row.get("url"),
    )


def _read(path: Path) -> Iterator[SourceRecord[ScrapingIndexRow]]:
    return read_jsonl(path, ScrapingIndexRow.__record_set__, ScrapingIndexRow.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[ScrapingIndexRow]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
