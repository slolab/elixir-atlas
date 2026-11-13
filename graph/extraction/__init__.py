"""Declare every extraction: its name, schema, extractor, the files it reads and how many it takes at once."""

from biotope.extraction import Extraction

from ._documents import (
    CORDIS_DOCUMENTS,
    DIRECTORY_PAGES,
    ELECTION_PAGES,
    ELIXIR_PAGES,
    EVENT_PAGES,
    INITIATIVE_DOCUMENTS,
    PLAN_DOCUMENTS,
    PLAN_LINK_DOCUMENTS,
    RECOMMENDATION_DOCUMENTS,
    ROLE_DOCUMENTS,
)
from .cordis import CordisParticipant, CordisParticipantReader, CordisProject, CordisProjectReader
from .elixir_pages import (
    ElectionCandidate,
    ElectionReader,
    ElixirEvent,
    ElixirEventReader,
    ElixirPage,
    ElixirPageReader,
    GroupDirectoryEntry,
    GroupDirectoryReader,
)
from .initiatives import InitiativeReader, InitiativeStatement
from .plan_links import PlanLink, PlanLinkReader
from .plans import PlanItem, PlanReader
from .recommendations import Recommendation, RecommendationReader
from .roles import RoleReader, RoleStatement


EXTRACTIONS: tuple[Extraction, ...] = (
    Extraction(name="cordis_projects", schema=CordisProject, extractor=CordisProjectReader, files=CORDIS_DOCUMENTS),
    Extraction(
        name="cordis_participants", schema=CordisParticipant, extractor=CordisParticipantReader, files=CORDIS_DOCUMENTS
    ),
    Extraction(
        name="initiative_statements",
        schema=InitiativeStatement,
        extractor=InitiativeReader,
        files=INITIATIVE_DOCUMENTS,
        parallel=16,
    ),
    Extraction(
        name="role_statements", schema=RoleStatement, extractor=RoleReader, files=ROLE_DOCUMENTS, parallel=16
    ),
    Extraction(name="plan_items", schema=PlanItem, extractor=PlanReader, files=PLAN_DOCUMENTS, parallel=16),
    Extraction(
        name="group_directory", schema=GroupDirectoryEntry, extractor=GroupDirectoryReader, files=DIRECTORY_PAGES
    ),
    Extraction(name="elixir_pages", schema=ElixirPage, extractor=ElixirPageReader, files=ELIXIR_PAGES),
    Extraction(
        name="election_candidates", schema=ElectionCandidate, extractor=ElectionReader, files=ELECTION_PAGES
    ),
    Extraction(name="elixir_events", schema=ElixirEvent, extractor=ElixirEventReader, files=EVENT_PAGES),
    Extraction(
        name="recommendations",
        schema=Recommendation,
        extractor=RecommendationReader,
        files=RECOMMENDATION_DOCUMENTS,
        parallel=16,
    ),
    Extraction(name="plan_links", schema=PlanLink, extractor=PlanLinkReader, files=PLAN_LINK_DOCUMENTS, parallel=16),
)
