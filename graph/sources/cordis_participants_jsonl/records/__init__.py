"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import CordisParticipantRow


SOURCE = SourceContract(
    name="cordis_participants_jsonl/cordis_participants_jsonl_cordis_participants",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/cordis_participants.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(CordisParticipantRow,),
)
