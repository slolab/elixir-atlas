"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import PerunAccount2


SOURCE = SourceContract(
    name="perun/export_2_csv_export_2",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/input/perun.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(PerunAccount2,),
)
