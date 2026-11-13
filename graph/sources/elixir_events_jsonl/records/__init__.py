"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import ElixirEventRow


SOURCE = SourceContract(
    name="elixir_events_jsonl/elixir_events_jsonl_elixir_events",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/extracted/elixir_events.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(ElixirEventRow,),
)
