"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import RecommendationRow


SOURCE = SourceContract(
    name="recommendations_jsonl/recommendations_jsonl_recommendations",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/recommendations.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(RecommendationRow,),
)
