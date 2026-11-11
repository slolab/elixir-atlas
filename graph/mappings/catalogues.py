from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import CatalogueLink, DocumentInfo, OutputLink, TopicEntry
from ..alignment.names import digest, list_item, one_line
from ..sources.catalogues.biotools.schema import BiotoolsTool
from ..sources.catalogues.europepmc_reviews.schema import EuropepmcReview
from ..sources.catalogues.f1000_items.schema import F1000Item
from ..sources.catalogues.tess_events.schema import TessEvent
from ..sources.catalogues.tess_materials.schema import TessMaterial
from ..sources.catalogues.zenodo_records.schema import ZenodoRecord
from ..topology import (
    Authored,
    CreditedForTool,
    Delivers,
    ElixirNodeId,
    EventFor,
    EventInNode,
    EventTopic,
    InitiativeId,
    MaterialFor,
    MaterialInNode,
    MaterialTopic,
    Output,
    OutputId,
    OutputOf,
    PersonId,
    PlanItemId,
    ReviewPaper,
    ReviewPaperId,
    SourceDocument,
    SourceDocumentId,
    Tool,
    ToolFor,
    ToolId,
    ToolInNode,
    Topic,
    TopicId,
    ToolTopic,
    TrainingEvent,
    TrainingEventId,
    TrainingMaterial,
    TrainingMaterialId,
)


def items(values: list[str]) -> list[str]:
    return list(dict.fromkeys(list_item(value) for value in values if value.strip()))


def doi_of(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lower().removeprefix("https://doi.org/").removeprefix("http://dx.doi.org/").removeprefix("doi:")


def make_tool(row: SourceRecord[BiotoolsTool], link: SourceRecord[CatalogueLink]) -> Iterator[
    Tool | ToolFor | ToolInNode | ToolTopic | CreditedForTool
]:
    value, tool_id = row.value, ToolId(link.value.item_id)
    yield Tool(
        id=tool_id,
        biotools_id=value.biotools_id,
        name=one_line(value.name),
        description=one_line(value.description),
        homepage=value.homepage,
        url=f"https://bio.tools/{value.biotools_id}",
        tool_types=items(value.tool_types),
        elixir_nodes=items(value.elixir_nodes),
        elixir_platforms=items(value.elixir_platforms),
        elixir_communities=items(value.elixir_communities),
        collections=items(value.collections),
        topics=items(value.topic_labels),
        last_update=value.last_update,
    )
    for initiative_id, tag in link.value.initiatives:
        yield ToolFor(id=f"tool_for:{digest(tool_id, initiative_id, tag)}", source=tool_id, target=InitiativeId(initiative_id), as_written=tag)
    for node_id, tag in link.value.nodes:
        yield ToolInNode(id=f"tool_in_node:{digest(tool_id, node_id, tag)}", source=tool_id, target=ElixirNodeId(node_id), as_written=tag)
    for topic_id in link.value.topics:
        yield ToolTopic(id=f"tool_topic:{digest(tool_id, topic_id)}", source=tool_id, target=TopicId(topic_id))
    for person_id, name in link.value.people:
        yield CreditedForTool(
            id=f"credited_for_tool:{digest(person_id, tool_id, name)}",
            source=PersonId(person_id),
            target=tool_id,
            name_as_written=name,
        )


def make_event(row: SourceRecord[TessEvent], link: SourceRecord[CatalogueLink]) -> Iterator[
    TrainingEvent | EventFor | EventInNode | EventTopic
]:
    value, event_id = row.value, TrainingEventId(link.value.item_id)
    yield TrainingEvent(
        id=event_id,
        tess_id=value.tess_id,
        title=one_line(value.title),
        url=value.url,
        start=value.start,
        end=value.end,
        event_types=items(value.event_types),
        online=value.online,
        city=value.city,
        country=value.country,
        organizer=one_line(value.organizer),
        host_institutions=items(value.host_institutions),
        keywords=items(value.keywords),
        topics=items(value.topic_labels),
        content_provider=link.value.provider,
        description=one_line(value.description),
    )
    for initiative_id, collection in link.value.initiatives:
        yield EventFor(
            id=f"event_for:{digest(event_id, initiative_id, collection)}",
            source=event_id,
            target=InitiativeId(initiative_id),
            collection=collection,
        )
    for node_id, _ in link.value.nodes:
        yield EventInNode(id=f"event_in_node:{digest(event_id, node_id)}", source=event_id, target=ElixirNodeId(node_id))
    for topic_id in link.value.topics:
        yield EventTopic(id=f"event_topic:{digest(event_id, topic_id)}", source=event_id, target=TopicId(topic_id))


def make_material(row: SourceRecord[TessMaterial], link: SourceRecord[CatalogueLink]) -> Iterator[
    TrainingMaterial | MaterialFor | MaterialInNode | MaterialTopic
]:
    value, material_id = row.value, TrainingMaterialId(link.value.item_id)
    yield TrainingMaterial(
        id=material_id,
        tess_id=value.tess_id,
        title=one_line(value.title),
        url=value.url,
        doi=doi_of(value.doi),
        authors=items(value.authors),
        resource_types=items(value.resource_types),
        date_published=value.date_published,
        keywords=items(value.keywords),
        topics=items(value.topic_labels),
        content_provider=link.value.provider,
        description=one_line(value.description),
    )
    for initiative_id, collection in link.value.initiatives:
        yield MaterialFor(
            id=f"material_for:{digest(material_id, initiative_id, collection)}",
            source=material_id,
            target=InitiativeId(initiative_id),
            collection=collection,
        )
    for node_id, _ in link.value.nodes:
        yield MaterialInNode(
            id=f"material_in_node:{digest(material_id, node_id)}", source=material_id, target=ElixirNodeId(node_id)
        )
    for topic_id in link.value.topics:
        yield MaterialTopic(id=f"material_topic:{digest(material_id, topic_id)}", source=material_id, target=TopicId(topic_id))


def output_edges(output_id: OutputId, link: OutputLink) -> Iterator[Authored | OutputOf | Delivers]:
    for person_id, position, name, affiliation in link.authors:
        yield Authored(
            id=f"authored:{digest(person_id, output_id, str(position))}",
            source=PersonId(person_id),
            target=output_id,
            position=position,
            name_as_written=name,
            affiliation=one_line(affiliation),
        )
    for initiative_id, basis in link.initiatives:
        yield OutputOf(
            id=f"output_of:{digest(output_id, initiative_id)}", source=output_id, target=InitiativeId(initiative_id), basis=basis
        )
    for plan_item_id, basis in link.plan_items:
        yield Delivers(
            id=f"delivers:{digest(output_id, plan_item_id)}", source=output_id, target=PlanItemId(plan_item_id), basis=basis
        )


def make_zenodo_output(row: SourceRecord[ZenodoRecord], link: SourceRecord[OutputLink]) -> Iterator[
    Output | Authored | OutputOf | Delivers
]:
    value, output_id = row.value, OutputId(link.value.output_id)
    yield Output(
        id=output_id,
        kind="zenodo_record",
        title=one_line(value.title),
        date=value.publication_date,
        doi=doi_of(value.doi),
        url=value.url or f"https://zenodo.org/records/{value.record_id}",
        resource_type=value.resource_type,
        version=one_line(value.version),
        keywords=items(value.keywords),
        communities=items(value.communities),
        grants=items([*value.grant_codes, *value.grant_acronyms]),
        authors=items(value.person_names),
        description=one_line(value.description),
    )
    yield from output_edges(output_id, link.value)


def make_f1000_output(row: SourceRecord[F1000Item], link: SourceRecord[OutputLink]) -> Iterator[
    Output | Authored | OutputOf | Delivers
]:
    value, output_id = row.value, OutputId(link.value.output_id)
    yield Output(
        id=output_id,
        kind=value.kind,
        title=one_line(value.title),
        date=value.date,
        doi=doi_of(value.doi),
        url=link.value.url,
        resource_type=None,
        version=None,
        keywords=items(value.subjects),
        communities=[],
        grants=[],
        authors=items(value.person_names),
        description=one_line(value.description),
    )
    yield from output_edges(output_id, link.value)


def make_review_paper(row: SourceRecord[EuropepmcReview]) -> Iterator[ReviewPaper]:
    value = row.value
    yield ReviewPaper(
        id=ReviewPaperId(f"europepmc:{value.epmc_id}"),
        title=one_line(value.title),
        journal=one_line(value.journal),
        year=value.pub_year,
        date=value.first_publication_date,
        doi=doi_of(value.doi),
        authors=items(value.person_names),
        keywords=items(value.keywords),
        mesh_terms=items(value.mesh_terms),
        abstract=one_line(value.abstract),
        cited_by_count=value.cited_by_count,
    )


def make_topic(entry: SourceRecord[TopicEntry]) -> Iterator[Topic]:
    value = entry.value
    yield Topic(id=TopicId(value.topic_id), label=value.label, uri=value.uri)


def make_source_document(info: SourceRecord[DocumentInfo]) -> Iterator[SourceDocument]:
    value = info.value
    yield SourceDocument(
        id=SourceDocumentId(value.document_id),
        path=value.path,
        url=value.url,
        retrieved_at=value.retrieved_at,
        source=value.source,
        content_type=value.content_type,
    )


TOOLS = Mapping(
    name="atlas:tool",
    function=make_tool,
    evidence=("bio.tools entries with at least one ELIXIR Node, Platform or Community tag; tags resolved to Nodes and groups by name.",),
)
EVENTS = Mapping(
    name="atlas:training_event",
    function=make_event,
    evidence=("Every TeSS event; TeSS Node and collection ids named by matching their counts to the TeSS facets.",),
)
MATERIALS = Mapping(
    name="atlas:training_material",
    function=make_material,
    evidence=("Every TeSS material; TeSS Node and collection ids named by matching their counts to the TeSS facets.",),
)
ZENODO_OUTPUTS = Mapping(
    name="atlas:output_zenodo",
    function=make_zenodo_output,
    evidence=("Every Zenodo record of the snapshot, deduplicated by record id; authors resolved to people.",),
)
F1000_OUTPUTS = Mapping(
    name="atlas:output_f1000",
    function=make_f1000_output,
    evidence=("Every item of the F1000Research ELIXIR Gateway in the snapshot; authors resolved to people.",),
)
REVIEW_PAPERS = Mapping(name="atlas:review_paper", function=make_review_paper, evidence=("Every Europe PMC review in the snapshot.",))
TOPICS = Mapping(name="atlas:topic", function=make_topic, evidence=("EDAM topics that bio.tools and TeSS assign.",))
SOURCE_DOCUMENTS = Mapping(
    name="atlas:source_document",
    function=make_source_document,
    evidence=("Each scraped document that a statement, role or plan item cites, with its URL from the scraping index.",),
)
