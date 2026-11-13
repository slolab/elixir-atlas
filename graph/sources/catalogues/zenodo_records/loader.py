from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import ZenodoRecord


def _decode(row: dict[str, Any]) -> ZenodoRecord:
    return ZenodoRecord(
        communities=row["communities"],
        concept_doi=row.get("concept_doi"),
        concept_record_id=row.get("concept_record_id"),
        contributor_affiliations=row["contributor_affiliations"],
        contributor_names=row["contributor_names"],
        contributor_orcids=row["contributor_orcids"],
        creator_affiliations=row["creator_affiliations"],
        person_names=row["creator_names"],
        orcids=row["creator_orcids"],
        description=row.get("description"),
        doi=row.get("doi"),
        file_names=row["file_names"],
        grant_acronyms=row["grant_acronyms"],
        grant_codes=row["grant_codes"],
        keywords=row["keywords"],
        publication_date=row.get("publication_date"),
        record_id=row["record_id"],
        resource_type=row.get("resource_type"),
        source_path=row["source_path"],
        source_paths=row["source_paths"],
        title=row.get("title"),
        url=row.get("url"),
        version=row.get("version"),
    )


def _read(path: Path) -> Iterator[SourceRecord[ZenodoRecord]]:
    return read_jsonl(path, ZenodoRecord.__record_set__, ZenodoRecord.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[ZenodoRecord]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
