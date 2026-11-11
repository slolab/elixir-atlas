"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import PerunAccount


SOURCE = SourceContract(
    name="perun/export_csv_export",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/input/perun.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(PerunAccount,),
)
