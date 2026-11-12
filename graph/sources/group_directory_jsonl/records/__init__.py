"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import GroupDirectoryRow


SOURCE = SourceContract(
    name="group_directory_jsonl/group_directory_jsonl_group_directory",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/group_directory.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(GroupDirectoryRow,),
)
