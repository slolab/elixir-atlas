"""Declare every extraction: its name, schema, extractor, the files it reads and how many it takes at once."""

from biotope.extraction import Extraction

from ._documents import CORDIS_DOCUMENTS, INITIATIVE_DOCUMENTS, PLAN_DOCUMENTS, ROLE_DOCUMENTS
from .cordis import CordisParticipant, CordisParticipantReader, CordisProject, CordisProjectReader
from .initiatives import InitiativeReader, InitiativeStatement
from .plans import PlanItem, PlanReader
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
)
