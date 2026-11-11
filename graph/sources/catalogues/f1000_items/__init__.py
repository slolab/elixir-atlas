"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import F1000Item


SOURCE = SourceContract(
    name="catalogues/f1000_items_jsonl_f1000_items",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/catalogues.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(F1000Item,),
)
