"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import ReviewDecision


SOURCE = SourceContract(
    name="review_decisions_csv/review_decisions_csv_review_decisions",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/input/review-decisions.csv.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(ReviewDecision,),
)
