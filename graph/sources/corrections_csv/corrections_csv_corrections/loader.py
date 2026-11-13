import csv
import hashlib
from collections.abc import Iterator
from pathlib import Path

from biotope.graph import Evidence, RunContext, SourceRecord

from ....paths import PROJECT_ROOT
from . import SOURCE
from .schema import Correction

ACTIONS = {"node": {"add", "remove"}, "role": {"add", "remove"}, "kind": {"set"}}


def _read(path: Path) -> Iterator[SourceRecord[Correction]]:
    artifact = path.relative_to(PROJECT_ROOT).as_posix()
    version = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline="", encoding="utf-8") as stream:
        for number, row in enumerate(csv.DictReader(stream, strict=True), start=2):
            values = {key: (value or "").strip() or None for key, value in row.items()}
            subject, prop, action = values.get("subject"), values.get("property"), values.get("action")
            if not subject or prop not in ACTIONS or action not in ACTIONS[prop]:
                raise ValueError(f"{artifact}: line {number}: needs a subject and a valid property and action")
            record = Correction(
                subject=subject,
                property=prop,
                action=action,
                target=values.get("target"),
                value=values.get("value"),
                role=values.get("role"),
                confirmed_by=values.get("confirmed_by"),
                date=values.get("date"),
                note=values.get("note"),
            )
            yield SourceRecord(record, (Evidence(artifact, version, Correction.__record_set__, f"line {number}"),))


def load(context: RunContext) -> Iterator[SourceRecord[Correction]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
