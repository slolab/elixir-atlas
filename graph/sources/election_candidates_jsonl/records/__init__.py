"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import ElectionCandidateRow


SOURCE = SourceContract(
    name="election_candidates_jsonl/election_candidates_jsonl_election_candidates",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/election_candidates.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(ElectionCandidateRow,),
)
