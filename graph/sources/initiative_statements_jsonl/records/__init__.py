"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import InitiativeStatementRow


SOURCE = SourceContract(
    name="initiative_statements_jsonl/initiative_statements_jsonl_initiative_statements",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/initiative_statements.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(InitiativeStatementRow,),
)
