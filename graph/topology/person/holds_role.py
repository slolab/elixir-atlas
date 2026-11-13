from dataclasses import dataclass, field
from typing import ClassVar

from ..initiative.node import InitiativeId
from .node import PersonId


@dataclass(frozen=True)
class HoldsRole:
    """A person's role in a group or project as one source states it; one edge per person, role and source."""

    schema_id: ClassVar[str] = "atlas:holds_role"
    id: str
    source: PersonId
    target: InitiativeId
    role: str = field(
        metadata={
            "description": "Role as written, e.g. 'Co-lead', 'WP4 co-leader', 'Community Liaison'."
        }
    )
    role_kind: str = field(
        metadata={
            "description": "lead, co_lead, deputy, chair, coordinator, liaison, work_package_lead, task_lead, contact, head_of_node, node_coordinator, staff, member, participant, candidate (a candidate in the Community co-lead election, from the election page; not a co-lead, and not by itself a member), unconfirmed_lead (another page, such as a Node website, names the person as a lead of a Community, Platform or Focus Group whose own ELIXIR page lists its leads without them; not a current lead, see the review item) or other. A role from data/input/corrections.csv was confirmed by a Node and wins over every other source. ELIXIR Hub staff whom a group page lists under 'Leadership' without a lead title are liaison. When an EU project's web page names more than three leads for the same task, they are recorded as participant."
        }
    )
    work_item: str | None = field(
        metadata={
            "description": "Work package, task, activity or project body (e.g. 'General Assembly', 'External Advisory Board') the role is in, as written."
        }
    )
    affiliation: str | None = field(
        metadata={"description": "The person's organisation as this source writes it."}
    )
    node_as_written: str | None = field(
        metadata={
            "description": "The Node this source associates with the person, as written."
        }
    )
    period: str | None = field(
        metadata={"description": "When the person holds the role, as written."}
    )
    effort: str | None = field(
        metadata={
            "description": "Time commitment as written; null when the source states none (time is rarely published)."
        }
    )
    funding: str = field(
        metadata={
            "description": "funded or in_kind only when the source states it for this person's work and the quoted evidence mentions funding; otherwise not_stated. An organisation's EU contribution does not make a person funded."
        }
    )
    evidence: str | None = field(
        metadata={
            "description": "Verbatim excerpt of the source, with email addresses replaced by [email]."
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
