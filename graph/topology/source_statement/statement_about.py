from dataclasses import dataclass
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import SourceStatementId


@dataclass(frozen=True)
class StatementAbout:
    """The statement is about this initiative."""

    schema_id: ClassVar[str] = "atlas:statement_about"
    id: str
    source: SourceStatementId
    target: InitiativeId
