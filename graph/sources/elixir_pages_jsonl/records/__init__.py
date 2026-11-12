"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import ElixirPageRow


SOURCE = SourceContract(
    name="elixir_pages_jsonl/elixir_pages_jsonl_elixir_pages",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/elixir_pages.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(ElixirPageRow,),
)
