from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import InvolvementRecord, NodeInvolvementRecord, PlanLinkRecord, SharedWork
from ..alignment.names import digest
from ..topology import ElixirNodeId, InitiativeId, InvolvedIn, NodeInvolvedIn, PersonId, PlanLinkedTo, SharesWorkWith


def make_involved_in(record: SourceRecord[InvolvementRecord]) -> Iterator[InvolvedIn]:
    value = record.value
    yield InvolvedIn(
        id=f"involved_in:{digest(value.person_id, value.initiative_id)}",
        source=PersonId(value.person_id),
        target=InitiativeId(value.initiative_id),
        leadership=value.leadership,
        roles=list(value.roles),
        plan_items=list(value.plan_items),
        outputs=list(value.outputs),
        tools=list(value.tools),
        nodes=list(value.nodes),
        organisations=list(value.organisations),
        bases=list(value.bases),
        source_urls=list(value.source_urls),
    )


def make_node_involved_in(record: SourceRecord[NodeInvolvementRecord]) -> Iterator[NodeInvolvedIn]:
    value = record.value
    yield NodeInvolvedIn(
        id=f"node_involved_in:{digest(value.node_id, value.initiative_id)}",
        source=ElixirNodeId(value.node_id),
        target=InitiativeId(value.initiative_id),
        bases=list(value.bases),
        listed_on_own_page=value.listed_on_own_page,
        initiative_kind=value.initiative_kind,
        period=value.period,
        period_status=value.period_status,
        beneficiaries=list(value.beneficiaries),
        people=list(value.people),
        node_site=value.node_site,
        limits=value.limits,
        plan_summary=value.plan_summary,
        leads_plan_items=list(value.leads_plan_items),
        works_on_plan_items=list(value.works_on_plan_items),
        sources=list(value.sources),
    )


def make_plan_linked_to(record: SourceRecord[PlanLinkRecord]) -> Iterator[PlanLinkedTo]:
    value = record.value
    yield PlanLinkedTo(
        id=f"plan_linked_to:{digest(value.source, value.target, value.direction, value.item or '', value.linked_item or '', value.located.document_id or '')}",
        source=InitiativeId(value.source),
        target=InitiativeId(value.target),
        direction=value.direction,
        item=value.item,
        item_id=value.item_id,
        linked_item=value.linked_item,
        linked_item_id=value.linked_item_id,
        relation=value.relation,
        quote=value.quote,
        source_url=value.located.url,
        source_document=value.located.document_id,
    )


def make_shares_work_with(record: SourceRecord[SharedWork]) -> Iterator[SharesWorkWith]:
    value = record.value
    yield SharesWorkWith(
        id=f"shares_work_with:{digest(value.source, value.target, value.via, value.item_id)}",
        source=InitiativeId(value.source),
        target=InitiativeId(value.target),
        via=value.via,
        item=value.item,
        item_id=value.item_id,
        source_url=value.source_url,
    )


INVOLVED_IN = Mapping(
    name="atlas:involved_in",
    function=make_involved_in,
    evidence=("One edge per person and initiative, gathered from their roles, plan items, authored outputs and credited tools.",),
)
NODE_INVOLVED_IN = Mapping(
    name="atlas:node_involved_in",
    function=make_node_involved_in,
    evidence=("One edge per Node and initiative, gathered from Node lists, EU beneficiaries in the Node's country, lead Nodes and the Node's people.",),
)
SHARES_WORK_WITH = Mapping(
    name="atlas:shares_work_with",
    function=make_shares_work_with,
    evidence=("Pairs of groups linked to the same project, output, tool, leader or resource, from the edges that link each group to it.",),
)
PLAN_LINKED_TO = Mapping(
    name="atlas:plan_linked_to",
    function=make_plan_linked_to,
    evidence=("One edge per stated link between work items of two initiatives, in both directions, from the plan_links extraction.",),
)
