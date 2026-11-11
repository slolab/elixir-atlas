"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import RoleStatementRow


SOURCE = SourceContract(
    name="role_statements_jsonl/role_statements_jsonl_role_statements",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/role_statements.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(RoleStatementRow,),
)
