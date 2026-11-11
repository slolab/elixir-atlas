import csv
import hashlib
from collections.abc import Iterator
from pathlib import Path

from biotope.graph import Evidence, RunContext, SourceRecord

from ....paths import PROJECT_ROOT
from . import SOURCE
from .schema import ReviewDecision


def _read(path: Path) -> Iterator[SourceRecord[ReviewDecision]]:
    artifact = path.relative_to(PROJECT_ROOT).as_posix()
    version = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline="", encoding="utf-8") as stream:
        for number, row in enumerate(csv.DictReader(stream, strict=True), start=2):
            review_id, decision = (row.get("review_id") or "").strip(), (row.get("decision") or "").strip()
            if not review_id or not decision:
                raise ValueError(f"{artifact}: line {number}: review_id and decision are both required")
            record = ReviewDecision(review_id=review_id, decision=decision)
            yield SourceRecord(record, (Evidence(artifact, version, ReviewDecision.__record_set__, f"line {number}"),))


def load(context: RunContext) -> Iterator[SourceRecord[ReviewDecision]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
