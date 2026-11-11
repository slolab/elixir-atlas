"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import CordisProjectRow


SOURCE = SourceContract(
    name="cordis_projects_jsonl/cordis_projects_jsonl_cordis_projects",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/cordis_projects.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(CordisProjectRow,),
)
