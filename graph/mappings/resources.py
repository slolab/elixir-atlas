from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import RecommendationLink, ResourceRecord
from ..alignment.names import digest, one_line
from ..sources.recommendations_jsonl.records.schema import RecommendationRow
from ..topology import InitiativeId, IsTool, Recommends, Resource, ResourceId, ToolId


def make_resource(record: SourceRecord[ResourceRecord]) -> Iterator[Resource | IsTool]:
    value = record.value
    resource_id = ResourceId(value.resource_id)
    yield Resource(id=resource_id, name=value.name, kind=value.kind, url=value.url)
    for tool_id, basis in value.tools:
        yield IsTool(id=f"is_tool:{digest(resource_id, tool_id)}", source=resource_id, target=ToolId(tool_id), basis=basis)


def make_recommends(row: SourceRecord[RecommendationRow], link: SourceRecord[RecommendationLink]) -> Iterator[Recommends]:
    value, located = row.value, link.value.located
    yield Recommends(
        id=f"recommends:{digest(value.id)}",
        source=InitiativeId(link.value.initiative_id),
        target=ResourceId(link.value.resource_id),
        basis="develops" if value.basis == "develops" else "recommends",
        resource_as_written=one_line(value.resource) or value.resource,
        purpose=one_line(value.purpose),
        url=value.url,
        evidence=one_line(link.value.evidence),
        source_url=located.url,
        retrieved_at=located.retrieved_at,
        source_document=located.document_id,
    )


RESOURCES = Mapping(
    name="atlas:resource",
    function=make_resource,
    evidence=("Resources that group pages and papers name, one per name after ignoring case and punctuation.",),
)
RECOMMENDS = Mapping(
    name="atlas:recommends",
    function=make_recommends,
    evidence=("One edge per extracted recommendation whose group resolves to an ELIXIR Community, Platform or Focus Group.",),
)
