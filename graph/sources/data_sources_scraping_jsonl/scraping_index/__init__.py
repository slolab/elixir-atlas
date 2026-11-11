"""Source registration; the schema and loader beside it are project-owned."""

from pathlib import Path

from biotope.graph import SourceContract

from .schema import ScrapingIndexRow


SOURCE = SourceContract(
    name="data_sources_scraping_jsonl/data_sources_scraping_jsonl_data_sources_scraping",
    metadata=Path(__file__).resolve().parent / "../../../../.biotope/datasets/data/input/data-sources-scraping.jsonl.jsonld",
    schema=Path(__file__).with_name("schema.py"),
    records=(ScrapingIndexRow,),
)
