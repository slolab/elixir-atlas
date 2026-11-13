from dataclasses import dataclass, field
from typing import ClassVar, NewType


SourceDocumentId = NewType("SourceDocumentId", str)


@dataclass(frozen=True)
class SourceDocument:
    """A scraped page, document or API response that a fact in the atlas comes from, with its public URL and
    retrieval date from the scraping index."""

    schema_id: ClassVar[str] = "atlas:source_document"
    id: SourceDocumentId
    path: str = field(
        metadata={
            "description": "Path of the saved copy in the project's data snapshot."
        }
    )
    url: str | None = field(metadata={"description": "Public URL."})
    retrieved_at: str | None = field(
        metadata={"description": "Retrieval time (ISO 8601 UTC)."}
    )
    source: str | None = field(
        metadata={
            "description": "Scraper source name, e.g. elixir, node-uk, zenodo-steers."
        }
    )
    content_type: str | None = field(metadata={"description": "Media type."})
    published: str | None = field(
        metadata={"description": "The page's own publication date (datePublished, YYYY-MM-DD), for ELIXIR website pages. A page date is not evidence of a group's activity."}
    )
    modified: str | None = field(
        metadata={"description": "The page's last-modified date (dateModified, YYYY-MM-DD), for ELIXIR website pages. An edit can be a correction or a layout change; it is not evidence of a group's activity."}
    )
