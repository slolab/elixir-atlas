from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import EdgeLink, RoleLink
from ..alignment.names import digest, list_item, one_line, without_emails
from ..sources.election_candidates_jsonl.records.schema import ElectionCandidateRow
from ..sources.role_statements_jsonl.records.schema import RoleStatementRow
from ..topology import (
    AffiliatedWith,
    ElixirNodeId,
    HoldsRole,
    InitiativeId,
    InNode,
    OrganisationId,
    PersonId,
    PlanItemId,
    WorksOnPlanItem,
)


def make_holds_role(row: SourceRecord[RoleStatementRow], link: SourceRecord[RoleLink]) -> Iterator[HoldsRole]:
    value, located = row.value, link.value.located
    yield HoldsRole(
        id=f"holds_role:{digest(value.id)}",
        source=PersonId(link.value.person_id),
        target=InitiativeId(link.value.initiative_id),
        role=one_line(value.role) or value.role,
        role_kind=link.value.role_kind,
        work_item=one_line(link.value.work_item),
        affiliation=one_line(value.affiliation),
        node_as_written=one_line(value.node),
        period=one_line(value.period),
        effort=one_line(value.effort),
        funding=link.value.funding,
        evidence=without_emails(one_line(link.value.evidence)),
        source_url=located.url,
        retrieved_at=located.retrieved_at,
        source_document=located.document_id,
    )


def make_candidate(row: SourceRecord[ElectionCandidateRow], link: SourceRecord[RoleLink]) -> Iterator[HoldsRole]:
    value, located = row.value, link.value.located
    note = f" ({value.note})" if value.note else ""
    yield HoldsRole(
        id=f"holds_role:{digest(value.id)}",
        source=PersonId(link.value.person_id),
        target=InitiativeId(link.value.initiative_id),
        role=f"Co-lead candidate{note}",
        role_kind="candidate",
        work_item=None,
        affiliation=one_line(value.affiliation),
        node_as_written=one_line(value.country),
        period=f"{value.year} co-lead election",
        effort=None,
        funding="not_stated",
        evidence=one_line(link.value.evidence),
        source_url=located.url,
        retrieved_at=located.retrieved_at,
        source_document=located.document_id,
    )


def edge_id(kind: str, link: EdgeLink) -> str:
    return f"{kind}:{digest(link.source, link.target, link.located.document_id or '', link.as_written, link.role or '')}"


def make_in_node(link: SourceRecord[EdgeLink]) -> Iterator[InNode]:
    value = link.value
    yield InNode(
        id=edge_id("in_node", value),
        source=PersonId(value.source),
        target=ElixirNodeId(value.target),
        as_written=list_item(value.as_written),
        role=one_line(value.role),
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


def make_affiliated_with(link: SourceRecord[EdgeLink]) -> Iterator[AffiliatedWith]:
    value = link.value
    yield AffiliatedWith(
        id=edge_id("affiliated_with", value),
        source=PersonId(value.source),
        target=OrganisationId(value.target),
        as_written=list_item(value.as_written),
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


def make_works_on_plan_item(link: SourceRecord[EdgeLink]) -> Iterator[WorksOnPlanItem]:
    value = link.value
    yield WorksOnPlanItem(
        id=edge_id("works_on_plan_item", value),
        source=PersonId(value.source),
        target=PlanItemId(value.target),
        role=value.role or "lead",
        as_written=list_item(value.as_written),
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


HOLDS_ROLE = Mapping(
    name="atlas:holds_role",
    function=make_holds_role,
    evidence=("One edge per extracted role statement whose holder is a person and whose place resolves to a group or project.",),
)
IN_NODE = Mapping(
    name="atlas:in_node",
    function=make_in_node,
    evidence=("Node positions and Node names stated next to a person, resolved against the closed list of Nodes.",),
)
AFFILIATED_WITH = Mapping(
    name="atlas:affiliated_with",
    function=make_affiliated_with,
    evidence=("Affiliations stated next to a person in a role statement.",),
)
WORKS_ON_PLAN_ITEM = Mapping(
    name="atlas:works_on_plan_item",
    function=make_works_on_plan_item,
    evidence=(
        "People named as leads or participants of a plan item, or holding a lead role in the work package or task of "
        "that code; more than three leads of one item are participants.",
    ),
)
CANDIDATES = Mapping(
    name="atlas:holds_role_candidate",
    function=make_candidate,
    evidence=("Candidates in the co-lead election table of the ELIXIR Communities election page.",),
)
