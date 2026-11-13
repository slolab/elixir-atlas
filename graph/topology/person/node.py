from dataclasses import dataclass, field
from typing import ClassVar, NewType


PersonId = NewType("PersonId", str)


@dataclass(frozen=True)
class Person:
    """A person named by at least one source: the Perun people export, ELIXIR and Node web pages, work plans and
    handbooks, CORDIS, Zenodo and F1000 records, or bio.tools credits.

    Mentions are joined into one person only on a shared ORCID iD, a shared email address, or the same full name
    after ignoring case, accents, punctuation and titles ('Surname, Given' is read as 'Given Surname'; other name
    orders are not joined), and only when no two different ORCID iDs or Perun accounts carry that name. Spelling variants such as 'Alex'/'Alexander' or a dropped middle name are NOT
    joined: they stay separate people and appear as an open person_match review_item until someone decides.
    Identifiers are minted from the name and are stable across builds while the name is."""

    schema_id: ClassVar[str] = "atlas:person"
    id: PersonId
    name: str = field(
        metadata={
            "description": "The person's name in the spelling most of their sources use, first name first."
        }
    )
    name_variants: list[str] = field(
        metadata={
            "description": "Every spelling of the name that a source uses for this person."
        }
    )
    orcids: list[str] = field(
        metadata={"description": "ORCID iDs that sources give for this person."}
    )
    email_domains: list[str] = field(
        metadata={
            "description": "Domains of the email addresses sources give for this person; the addresses are used for matching and are not exported."
        }
    )
    in_perun: bool = field(
        metadata={
            "description": "True when the Perun people export (1,622 ELIXIR AAI accounts of one ELIXIR group export whose group is not recorded) has an account with this name or email."
        }
    )
    perun_organisation: str | None = field(
        metadata={
            "description": "The organisation field of the person's Perun account; often a login provider (ORCID, Google, LinkedIn) rather than an employer."
        }
    )
    source_kinds: list[str] = field(
        metadata={
            "description": "Kinds of source that name the person: perun, role_statement, plan_item, election_candidate, zenodo, f1000, biotools."
        }
    )
    identity_basis: list[str] = field(
        metadata={
            "description": "How mentions were joined: orcid, email, exact_name, single_mention or decision (a reviewed review_item)."
        }
    )
