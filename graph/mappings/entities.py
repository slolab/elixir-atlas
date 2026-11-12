from collections.abc import Iterator

from biotope.graph import Mapping, SourceRecord

from ..alignment.names import list_item
from ..alignment.nodes import NodeEntry
from ..alignment.organisations import OrganisationIdentity
from ..alignment.people import PersonIdentity
from ..alignment.reviews import Review
from ..topology import ElixirNode, ElixirNodeId, Organisation, OrganisationId, Person, PersonId, ReviewItem, ReviewItemId


def make_person(person: SourceRecord[PersonIdentity]) -> Iterator[Person]:
    value = person.value
    yield Person(
        id=PersonId(value.person_id),
        name=value.name,
        name_variants=list(dict.fromkeys(list_item(name) for name in value.name_variants)),
        orcids=list(value.orcids),
        email_domains=list(value.email_domains),
        in_perun=value.in_perun,
        perun_organisation=value.perun_organisation,
        source_kinds=list(value.source_kinds),
        identity_basis=list(value.identity_basis),
    )


def make_elixir_node(node: SourceRecord[NodeEntry]) -> Iterator[ElixirNode]:
    value = node.value
    yield ElixirNode(
        id=ElixirNodeId(value.node_id),
        name=value.name,
        kind=value.kind,
        country=value.country,
        aliases=sorted(set(value.aliases)),
    )


def make_organisation(organisation: SourceRecord[OrganisationIdentity]) -> Iterator[Organisation]:
    value = organisation.value
    yield Organisation(
        id=OrganisationId(value.organisation_id),
        name=value.name,
        name_variants=list(dict.fromkeys(list_item(name) for name in value.name_variants)),
        country=value.country,
        activity_type=value.activity_type,
    )


def make_review_item(item: SourceRecord[Review]) -> Iterator[ReviewItem]:
    value = item.value
    yield ReviewItem(
        id=ReviewItemId(value.review_id),
        kind=value.kind,
        question=value.question,
        subjects=list(value.subjects),
        subject_names=list(value.subject_names),
        property=value.property,
        options=list(value.options),
        status=value.status,
        decision=value.decision,
    )


PEOPLE = Mapping(
    name="atlas:person",
    function=make_person,
    evidence=("One person per resolved identity; mentions joined on ORCID, email or a unique exact name.",),
)
ELIXIR_NODES = Mapping(name="atlas:elixir_node", function=make_elixir_node, evidence=("Closed list of ELIXIR Nodes and the Hub.",))
ORGANISATIONS = Mapping(name="atlas:organisation", function=make_organisation, evidence=("CORDIS participants and stated affiliations, joined on equal names.",))
REVIEW_ITEMS = Mapping(name="atlas:review_item", function=make_review_item, evidence=("Open questions of identity and conflicting values.",))
