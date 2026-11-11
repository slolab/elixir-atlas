from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import EuropepmcReview


def _decode(row: dict[str, Any]) -> EuropepmcReview:
    return EuropepmcReview(
        abstract=row.get("abstract"),
        person_names=row["author_names"],
        orcids=row["author_orcids"],
        cited_by_count=row.get("cited_by_count"),
        doi=row.get("doi"),
        epmc_id=row["epmc_id"],
        first_publication_date=row.get("first_publication_date"),
        journal=row.get("journal"),
        keywords=row["keywords"],
        mesh_terms=row["mesh_terms"],
        pmid=row.get("pmid"),
        pub_year=row.get("pub_year"),
        source_path=row["source_path"],
        title=row.get("title"),
    )


def _read(path: Path) -> Iterator[SourceRecord[EuropepmcReview]]:
    return read_jsonl(path, EuropepmcReview.__record_set__, EuropepmcReview.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[EuropepmcReview]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
