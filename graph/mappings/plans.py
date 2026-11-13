from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import PlanItemRecord
from ..alignment.names import digest, list_item, one_line
from ..topology import InitiativeId, PlanItem, PlanItemId, PlanItemOf, PlanItemTopic, TopicId


def make_plan_item(record: SourceRecord[PlanItemRecord]) -> Iterator[PlanItem | PlanItemOf | PlanItemTopic]:
    value = record.value
    plan_item_id = PlanItemId(value.plan_item_id)
    yield PlanItem(
        id=plan_item_id,
        kind=value.kind,
        code=one_line(value.code),
        label=one_line(value.label) or value.label,
        description=one_line(value.description),
        parent=one_line(value.parent),
        date=value.date,
        date_as_written=one_line(value.date_as_written),
        date_statements=[list_item(item) for item in value.date_statements],
        status=value.status,
        leads=[list_item(item) for item in value.leads],
        participants=[list_item(item) for item in value.participants],
        tools=list(value.tools),
        effort=one_line(value.effort),
        link=value.link,
        sources=list(value.sources),
        evidence=one_line(value.evidence),
    )
    yield PlanItemOf(id=f"plan_item_of:{plan_item_id}", source=plan_item_id, target=InitiativeId(value.initiative_id))
    for topic_id in value.topics:
        yield PlanItemTopic(id=f"plan_item_topic:{digest(plan_item_id, topic_id)}", source=plan_item_id, target=TopicId(topic_id))


PLAN_ITEMS = Mapping(
    name="atlas:plan_item",
    function=make_plan_item,
    evidence=("Plan items of one initiative with the same code, or the same kind and title, are joined across documents.",),
)
