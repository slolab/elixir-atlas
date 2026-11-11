from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biotope.graph import RunContext, SourceRecord

from .._files import read_jsonl
from . import SOURCE
from .schema import BiotoolsTool


def _decode(row: dict[str, Any]) -> BiotoolsTool:
    return BiotoolsTool(
        addition_date=row.get("addition_date"),
        biotools_id=row["biotools_id"],
        collections=row["collections"],
        credit_emails=row["credit_emails"],
        person_names=row["credit_names"],
        orcids=row["credit_orcids"],
        credit_types=row["credit_types"],
        description=row.get("description"),
        elixir_communities=row["elixir_communities"],
        elixir_nodes=row["elixir_nodes"],
        elixir_platforms=row["elixir_platforms"],
        homepage=row.get("homepage"),
        last_update=row.get("last_update"),
        name=row.get("name"),
        publication_dois=row["publication_dois"],
        source_path=row["source_path"],
        tool_types=row["tool_types"],
        topic_labels=row["topic_labels"],
        edam_topic_uris=row["topic_uris"],
    )


def _read(path: Path) -> Iterator[SourceRecord[BiotoolsTool]]:
    return read_jsonl(path, BiotoolsTool.__record_set__, BiotoolsTool.__missing_values__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[BiotoolsTool]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
