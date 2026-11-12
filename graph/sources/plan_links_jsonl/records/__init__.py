"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import PlanLinkRow


SOURCE = SourceContract(
    name="plan_links_jsonl/plan_links_jsonl_plan_links",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/plan_links.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(PlanLinkRow,),
)
