from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal

from biotope.extraction import Document, Schema

from ._llm import MODEL, LlmExtractor, chunks
from ._reading import document_text, person_links, squashed

RoleKind = Literal[
    "lead",
    "co_lead",
    "deputy",
    "chair",
    "coordinator",
    "liaison",
    "work_package_lead",
    "task_lead",
    "contact",
    "head_of_node",
    "node_coordinator",
    "staff",
    "member",
    "participant",
    "other",
]

PlaceKind = Literal["group", "project", "work_package", "task", "node", "hub", "governance_body", "organisation", "other"]


@dataclass(frozen=True, kw_only=True)
class RoleStatement:
    """A named person's role, membership or position in ELIXIR, as one document states it: leads, co-leads,
    chairs, coordinators, Hub liaisons, work package and task leaders and deputies, contact persons, Heads of Node,
    Node coordinators and staff, and members and participants of groups and projects. One record per person, role
    and place. Leave out authors of cited works, people only thanked or quoted, and roles without a named person."""

    __record_key__: ClassVar[tuple[str, ...]] = ("person", "place", "role")

    person: str = field(
        metadata={"description": "The person's full name as written, without titles such as Dr or Prof."}
    )
    role: str = field(
        metadata={
            "description": "The role as written, e.g. 'Co-lead', 'WP4 co-leader', 'Platform Coordinator "
            "(interim)', 'Head of Node'; 'member' when the document lists the person without a role."
        }
    )
    role_kind: RoleKind = field(
        metadata={
            "description": "The kind of role. liaison is a Hub officer supporting a group; staff is employment "
            "at a Node or the Hub; member and participant are for people listed without a leading role."
        }
    )
    place: str = field(
        metadata={
            "description": "The group, project, work package, task, Node, Hub or body where the person holds the "
            "role, as written, e.g. 'Systems Biology Community', 'ELIXIR-STEERS', 'ELIXIR Switzerland'. For a "
            "work package or task, the project it belongs to."
        }
    )
    place_kind: PlaceKind = field(metadata={"description": "What kind of place the role is held in."})
    work_item: str | None = field(
        metadata={
            "description": "Code and title of the work package, task or activity the role is in, e.g. "
            "'WP4 Multi-Cloud Infrastructure Deployment', 'Task 4.2'."
        }
    )
    affiliation: str | None = field(metadata={"description": "The person's organisation, as written."})
    node: str | None = field(
        metadata={
            "description": "The ELIXIR Node the document associates with the person, e.g. 'ELIXIR Slovenia' or "
            "'ELIXIR Hub', as written."
        }
    )
    period: str | None = field(metadata={"description": "When the person holds the role, as written."})
    effort: str | None = field(
        metadata={
            "description": "Time the person commits to the role, as written: FTE, person-months or percent. "
            "Never estimated."
        }
    )
    funding: Literal["funded", "in_kind", "not_stated"] = field(
        metadata={
            "description": "funded or in_kind only when the document states it for this person's work in this "
            "role; otherwise not_stated. Funding of the person's organisation does not count."
        }
    )
    email: str | None = field(metadata={"description": "The person's email address, if the document gives it."})


RECALL = (
    "This document links the following people, but no record names them yet: {names}. Return a record for each "
    "role or membership the document states for them, including the heading or list they appear under. Return no "
    "record for a person the document only mentions, thanks or cites."
)


def names_match(linked: str, person: str) -> bool:
    left, right = squashed(linked), squashed(person)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    first, second = [squashed(word) for word in linked.split()], [squashed(word) for word in person.split()]
    return first[-1] == second[-1] and (first[0].startswith(second[0]) or second[0].startswith(first[0]))


def unmatched(linked: list[str], records: list[dict[str, Any]]) -> list[str]:
    people = [str(record["person"]["value"]) for record in records]
    return [name for name in linked if not any(names_match(name, person) for person in people)]


class RoleReader(LlmExtractor):
    name = "role-reader"
    version = "2"
    settings = {"model": MODEL, "reasoning": "low"}
    instructions = (
        "Tables of work packages, tasks and partners often name a lead and a deputy per item: give each person "
        "their own record. A 'WP Partnership' or partner list names everyone in the work package, often as "
        "'<partner code> - <name>': every listed person gets a member record for that work package, or for each "
        "activity the list names, besides any lead record. A person profile page gives one record per role or group it lists for the person. "
        "Names of Nodes are often written as 'ELIXIR <country>' or as the Node's own name, such as de.NBI, "
        "BioData.pt, SIB, IFB, INB or CSC; copy them as written. People listed under a heading such as "
        "'Leadership' or 'Leadership and Hub liaison' lead that group (lead or co_lead) unless the page marks them "
        "as liaison or coordinator; a label such as 'Deputy Head of Node' next to their name is their Node "
        "position, which gets its own record with the Node as place."
    )

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        records = super().extract(document, schema)
        text = document_text(document.path)
        missing = [name for name in unmatched(person_links(document.path), records) if squashed(name) in squashed(text)]
        if not missing:
            return records
        note = RECALL.format(names="; ".join(missing))
        haystack = squashed(text)
        known = {tuple(record[name]["value"] for name in schema.key) for record in records}
        for part in chunks(text):
            if not any(squashed(name) in squashed(part) for name in missing):
                continue
            for raw in self.ask(schema, document, part, note):
                record = self.convert(raw, schema, haystack)
                key = tuple(record[name]["value"] for name in schema.key)
                if key not in known and any(names_match(name, str(record["person"]["value"])) for name in missing):
                    known.add(key)
                    records.append(record)
        return records
