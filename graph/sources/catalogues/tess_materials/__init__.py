"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import TessMaterial


SOURCE = SourceContract(
    name="catalogues/tess_materials_jsonl_tess_materials",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/catalogues.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(TessMaterial,),
)
