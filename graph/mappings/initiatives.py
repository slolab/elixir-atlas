from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.links import BecameLink, EdgeLink, InitiativeRecord, ParticipationLink, StatementLink
from ..alignment.names import digest, list_item, one_line
from ..sources.cordis_participants_jsonl.records.schema import CordisParticipantRow
from ..sources.initiative_statements_jsonl.records.schema import InitiativeStatementRow
from ..topology import (
    Became,
    ElixirNodeId,
    Initiative,
    InitiativeId,
    InitiativeTopic,
    OrganisationId,
    ParticipatesIn,
    RelatedTo,
    SourceStatement,
    SourceStatementId,
    StatementAbout,
    TakesPartIn,
    TopicId,
)


def items(values: list[str] | tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(list_item(value) for value in values if value.strip()))


def make_initiative(record: SourceRecord[InitiativeRecord]) -> Iterator[Initiative]:
    value = record.value
    yield Initiative(
        id=InitiativeId(value.initiative_id),
        name=value.name,
        acronym=value.acronym,
        kind=value.kind,
        family=value.family,
        aliases=items(value.aliases),
        pages=list(value.pages),
        identity_basis=list(value.identity_basis),
        start=value.start,
        end=value.end,
        status=value.status,
        summary=one_line(value.summary),
        outcomes=items(value.outcomes),
        contacts=items(value.contacts),
        grant_id=value.grant_id,
        total_cost_eur=value.total_cost_eur,
        eu_contribution_eur=value.eu_contribution_eur,
        join_url=value.join_url,
        joining=one_line(value.joining),
        programme=value.programme,
        period_status=value.period_status,
        recent_activity=list(value.recent_activity),
        leaders=list(value.leaders),
        limits=list(value.limits),
        scope=value.scope,
        latest_own_activity=value.latest_own_activity,
        latest_activity=value.latest_activity,
    )


def make_became(link: SourceRecord[BecameLink]) -> Iterator[Became]:
    value = link.value
    yield Became(
        id=f"became:{digest(value.source, value.target)}",
        source=InitiativeId(value.source),
        target=InitiativeId(value.target),
        date=value.date,
        evidence=one_line(value.evidence),
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


def make_source_statement(
    row: SourceRecord[InitiativeStatementRow], link: SourceRecord[StatementLink]
) -> Iterator[SourceStatement | StatementAbout | InitiativeTopic]:
    value, located = row.value, link.value.located
    statement_id = SourceStatementId(link.value.statement_id)
    initiative_id = InitiativeId(link.value.initiative_id)
    yield SourceStatement(
        id=statement_id,
        name_as_written=one_line(value.name) or value.name,
        acronym=one_line(value.acronym),
        kind=value.kind,
        coverage=value.coverage,
        status=value.status,
        period=one_line(value.period),
        start=value.start,
        end=value.end,
        summary=one_line(value.summary),
        outcomes=items(value.outcomes),
        nodes=items(value.nodes),
        leads=items(value.leads),
        related=items(value.related),
        contacts=items(value.contacts),
        links=items(value.links),
        funding=one_line(value.funding),
        evidence=one_line(link.value.evidence),
        source_url=located.url,
        retrieved_at=located.retrieved_at,
        source_document=located.document_id,
    )
    yield StatementAbout(id=f"statement_about:{statement_id}", source=statement_id, target=initiative_id)
    for topic_id in link.value.topics:
        yield InitiativeTopic(
            id=f"initiative_topic:{digest(initiative_id, topic_id, statement_id)}",
            source=initiative_id,
            target=TopicId(topic_id),
            evidence=one_line(link.value.evidence),
            source_url=located.url,
            retrieved_at=located.retrieved_at,
            source_document=located.document_id,
        )


def make_takes_part_in(link: SourceRecord[EdgeLink]) -> Iterator[TakesPartIn]:
    value = link.value
    yield TakesPartIn(
        id=f"takes_part_in:{digest(value.source, value.target, value.located.document_id or '', value.as_written, value.basis)}",
        source=ElixirNodeId(value.source),
        target=InitiativeId(value.target),
        as_written=list_item(value.as_written),
        basis=value.basis,
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


def make_related_to(link: SourceRecord[EdgeLink]) -> Iterator[RelatedTo]:
    value = link.value
    yield RelatedTo(
        id=f"related_to:{digest(value.source, value.target, value.located.document_id or '', value.as_written, value.basis)}",
        source=InitiativeId(value.source),
        target=InitiativeId(value.target),
        as_written=list_item(value.as_written),
        direction="reverse" if value.basis == "reverse" else "stated",
        quote=value.quote,
        source_url=value.located.url,
        retrieved_at=value.located.retrieved_at,
        source_document=value.located.document_id,
    )


def make_participation(
    row: SourceRecord[CordisParticipantRow], link: SourceRecord[ParticipationLink]
) -> Iterator[ParticipatesIn]:
    value, located = row.value, link.value.located
    yield ParticipatesIn(
        id=f"participates_in:{digest(value.id)}",
        source=OrganisationId(link.value.organisation_id),
        target=InitiativeId(link.value.initiative_id),
        participation=value.participation,
        participation_ended=value.participation_ended,
        net_eu_contribution_eur=value.net_eu_contribution_eur,
        total_cost_eur=value.total_cost_eur,
        source_url=located.url,
        retrieved_at=located.retrieved_at,
        source_document=located.document_id,
    )


INITIATIVES = Mapping(
    name="atlas:initiative",
    function=make_initiative,
    evidence=("One initiative per resolved identity; values are those its sources agree on.",),
)
SOURCE_STATEMENTS = Mapping(
    name="atlas:source_statement",
    function=make_source_statement,
    evidence=("One statement per extracted initiative record, linked to its resolved initiative.",),
)
TAKES_PART_IN = Mapping(
    name="atlas:takes_part_in",
    function=make_takes_part_in,
    evidence=(
        "Nodes named by a statement or a plan item of the initiative, resolved against the closed list of Nodes "
        "(own_page when the statement is the initiative's own main page); and, as lead_node, the Nodes of the current "
        "leads that a group's own page names.",
    ),
)
BECAME = Mapping(
    name="atlas:became",
    function=make_became,
    evidence=("Transitions the ELIXIR directory pages and archived group pages state, resolved to initiatives by name.",),
)
RELATED_TO = Mapping(
    name="atlas:related_to",
    function=make_related_to,
    evidence=("Related groups and projects a statement names, resolved by page, name or acronym; each stored in both directions.",),
)
PARTICIPATIONS = Mapping(
    name="atlas:participates_in",
    function=make_participation,
    evidence=("CORDIS participant lists of the EU projects in the snapshot.",),
)
