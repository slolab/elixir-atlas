from dataclasses import dataclass, field
from typing import ClassVar, NewType


SourceStatementId = NewType("SourceStatementId", str)


@dataclass(frozen=True)
class SourceStatement:
    """What one page or document states about one group or project, exactly as extracted from it with a language
    model (openai/gpt-6.1-terra) and checked against a verbatim quote. Compare the statements of one initiative to
    find gaps, changes and conflicts, and use source_url and retrieved_at to cite each detail."""

    schema_id: ClassVar[str] = "atlas:source_statement"
    id: SourceStatementId
    name_as_written: str = field(
        metadata={"description": "The name as this source writes it."}
    )
    acronym: str | None = field(metadata={"description": "Acronym this source gives."})
    kind: str = field(
        metadata={"description": "What this source says it is (see initiative.kind)."}
    )
    coverage: str = field(
        metadata={
            "description": "described when the source is mainly about it; listed when it only lists it."
        }
    )
    status: str = field(
        metadata={
            "description": "Status this source states: current, completed, planned or not_stated."
        }
    )
    period: str | None = field(metadata={"description": "Period exactly as written."})
    start: str | None = field(
        metadata={
            "description": "Start of the stated period (YYYY, YYYY-MM or YYYY-MM-DD)."
        }
    )
    end: str | None = field(metadata={"description": "End of the stated period."})
    summary: str | None = field(
        metadata={"description": "The source's description of it, verbatim."}
    )
    outcomes: list[str] = field(
        metadata={"description": "Outcomes and objectives the source lists."}
    )
    nodes: list[str] = field(
        metadata={"description": "Nodes the source says take part, as written."}
    )
    leads: list[str] = field(
        metadata={
            "description": "Leads or coordinators the source names, as written (people, organisations or Nodes)."
        }
    )
    related: list[str] = field(
        metadata={
            "description": "Related groups, projects or tiers the source names, as written."
        }
    )
    contacts: list[str] = field(
        metadata={"description": "Contacts and join links the source gives."}
    )
    links: list[str] = field(
        metadata={"description": "URLs of outputs and resources the source gives."}
    )
    funding: str | None = field(
        metadata={"description": "Funding statement as written."}
    )
    evidence: str | None = field(
        metadata={
            "description": "Verbatim excerpt of the source supporting the statement, prefixed with 'page N:' for PDFs."
        }
    )
    source_url: str | None = field(
        metadata={
            "description": "URL of the page or document that states this, from the scraping index."
        }
    )
    retrieved_at: str | None = field(
        metadata={
            "description": "When that page or document was retrieved (ISO 8601 UTC)."
        }
    )
    source_document: str | None = field(
        metadata={
            "description": "Identifier of that document in the source_document table."
        }
    )
