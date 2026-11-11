"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import EuropepmcReview


SOURCE = SourceContract(
    name="catalogues/europepmc_reviews_jsonl_europepmc_reviews",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/catalogues.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(EuropepmcReview,),
)
