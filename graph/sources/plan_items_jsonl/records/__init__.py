"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import PlanItemRow


SOURCE = SourceContract(
    name="plan_items_jsonl/plan_items_jsonl_plan_items",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/plan_items.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(PlanItemRow,),
)
