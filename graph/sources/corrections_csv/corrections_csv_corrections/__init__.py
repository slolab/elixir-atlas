"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import Correction


SOURCE = SourceContract(
    name="corrections_csv/corrections_csv_corrections",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/input/corrections.csv.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(Correction,),
)
