"""Register each node from topology/<node>/node.py and each edge from topology/<source node>/<edge>.py."""

from biotope.graph import Topology

from .person.node import Person, PersonId
from .elixir_node.node import ElixirNode, ElixirNodeId
from .organisation.node import Organisation, OrganisationId
from .initiative.node import Initiative, InitiativeId
from .source_statement.node import SourceStatement, SourceStatementId
from .plan_item.node import PlanItem, PlanItemId
from .tool.node import Tool, ToolId
from .event.node import Event, EventId
from .training_material.node import TrainingMaterial, TrainingMaterialId
from .output.node import Output, OutputId
from .review_paper.node import ReviewPaper, ReviewPaperId
from .topic.node import Topic, TopicId
from .source_document.node import SourceDocument, SourceDocumentId
from .review_item.node import ReviewItem, ReviewItemId
from .resource.node import Resource, ResourceId
from .person.holds_role import HoldsRole
from .person.works_on_plan_item import WorksOnPlanItem
from .person.involved_in import InvolvedIn
from .person.in_node import InNode
from .person.affiliated_with import AffiliatedWith
from .person.authored import Authored
from .person.credited_for_tool import CreditedForTool
from .elixir_node.takes_part_in import TakesPartIn
from .elixir_node.node_involved_in import NodeInvolvedIn
from .organisation.participates_in import ParticipatesIn
from .initiative.plan_linked_to import PlanLinkedTo
from .initiative.related_to import RelatedTo
from .initiative.shares_work_with import SharesWorkWith
from .initiative.became import Became
from .initiative.part_of import PartOf
from .initiative.recommends import Recommends
from .resource.is_tool import IsTool
from .initiative.initiative_topic import InitiativeTopic
from .source_statement.statement_about import StatementAbout
from .plan_item.plan_item_of import PlanItemOf
from .plan_item.plan_item_topic import PlanItemTopic
from .tool.tool_for import ToolFor
from .tool.tool_in_node import ToolInNode
from .tool.tool_topic import ToolTopic
from .event.event_for import EventFor
from .event.event_in_node import EventInNode
from .event.event_topic import EventTopic
from .training_material.material_for import MaterialFor
from .training_material.material_in_node import MaterialInNode
from .training_material.material_topic import MaterialTopic
from .output.output_of import OutputOf
from .output.delivers import Delivers


TOPOLOGY = Topology(
    nodes=(
        Person,
        ElixirNode,
        Organisation,
        Initiative,
        SourceStatement,
        PlanItem,
        Tool,
        Event,
        TrainingMaterial,
        Output,
        ReviewPaper,
        Topic,
        SourceDocument,
        ReviewItem,
        Resource,
    ),
    edges=(
        HoldsRole,
        WorksOnPlanItem,
        InvolvedIn,
        NodeInvolvedIn,
        SharesWorkWith,
        InNode,
        AffiliatedWith,
        Authored,
        CreditedForTool,
        TakesPartIn,
        ParticipatesIn,
        PlanLinkedTo,
        RelatedTo,
        Became,
        PartOf,
        Recommends,
        IsTool,
        InitiativeTopic,
        StatementAbout,
        PlanItemOf,
        PlanItemTopic,
        ToolFor,
        ToolInNode,
        ToolTopic,
        EventFor,
        EventInNode,
        EventTopic,
        MaterialFor,
        MaterialInNode,
        MaterialTopic,
        OutputOf,
        Delivers,
    ),
)

__all__ = [
    "InvolvedIn",
    "NodeInvolvedIn",
    "SharesWorkWith",
    "Person",
    "PersonId",
    "ElixirNode",
    "ElixirNodeId",
    "Organisation",
    "OrganisationId",
    "Initiative",
    "InitiativeId",
    "SourceStatement",
    "SourceStatementId",
    "PlanItem",
    "PlanItemId",
    "Tool",
    "ToolId",
    "Event",
    "EventId",
    "TrainingMaterial",
    "TrainingMaterialId",
    "Output",
    "OutputId",
    "ReviewPaper",
    "ReviewPaperId",
    "Topic",
    "TopicId",
    "SourceDocument",
    "SourceDocumentId",
    "ReviewItem",
    "ReviewItemId",
    "Resource",
    "ResourceId",
    "HoldsRole",
    "WorksOnPlanItem",
    "InNode",
    "AffiliatedWith",
    "Authored",
    "CreditedForTool",
    "TakesPartIn",
    "ParticipatesIn",
    "PlanLinkedTo",
    "RelatedTo",
    "Became",
    "PartOf",
    "Recommends",
    "IsTool",
    "InitiativeTopic",
    "StatementAbout",
    "PlanItemOf",
    "PlanItemTopic",
    "ToolFor",
    "ToolInNode",
    "ToolTopic",
    "EventFor",
    "EventInNode",
    "EventTopic",
    "MaterialFor",
    "MaterialInNode",
    "MaterialTopic",
    "OutputOf",
    "Delivers",
    "TOPOLOGY",
]
