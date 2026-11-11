"""Shared terms: meanings that fields of several sources bind to.

A source schema binds its own fields with ``source_field(..., term=TERM)``. Bindings,
value aliases and missing-value tokens stay with each source; matching column names
establish no equivalence. A preserved field needs no term until it is aligned.
"""

from biotope.graph import Term


PERSON_NAME = Term(
    "person_name",
    "One person's name as the source writes it, in any order or spelling; not resolved to an identity.",
)
PERSON_NAMES = Term(
    "person_names",
    "Names of the people credited, as the source writes them, in the source's order; not resolved to identities.",
)
ORCIDS = Term(
    "orcids",
    "ORCID iDs of the people credited, aligned position by position with person_names; empty where none is given.",
)
EMAIL = Term("email", "One person's email address as the source gives it; used to match people, never exported.")
DOI = Term("doi", "Digital Object Identifier of the item, as the source gives it (with or without a resolver prefix).")
EDAM_TOPIC_URIS = Term("edam_topic_uris", "EDAM topic URIs the source assigns to the item.")

TERMS: tuple[Term, ...] = (PERSON_NAME, PERSON_NAMES, ORCIDS, EMAIL, DOI, EDAM_TOPIC_URIS)
