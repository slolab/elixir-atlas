"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import NodePageRoleRow


SOURCE = SourceContract(
    name="node_page_roles_jsonl/node_page_roles_jsonl_node_page_roles",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/node_page_roles.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(NodePageRoleRow,),
)
