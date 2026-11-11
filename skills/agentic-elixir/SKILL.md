---
name: agentic-elixir
description: Answer questions about ELIXIR Communities, Node commitments and project portfolios, research resources, and community roadmaps or handovers using the public ELIXIR Atlas. Use for finding connections between people, projects, plans, outputs, tools and training. Not for the Elixir programming language.
---

# Agentic ELIXIR

Use the public Atlas to investigate the user's question. Read [references/api.md](references/api.md) for requests, response fields and routes through the data. No credentials or local dataset are needed.

## Search and follow connections

1. Identify the relevant topic, people, Node or Community, and time period. Resolve named entities before exploring their connections.
2. Enrich topic searches with a few short variants: synonyms, acronyms, alternative spellings and terms likely to occur in the sources. For example, try `genome-scale metabolic modelling`, `metabolic modeling`, `constraint-based modelling` and `flux balance analysis`. These are retrieval hypotheses, not evidence.
3. Search variants separately and refine using terminology in useful results. Ordinary query words are combined with AND, so appending synonyms narrows the search. Use type filters to avoid having training records crowd out projects or tools. Deduplicate by record type and ID; stop expanding when results stop adding useful evidence.
4. Check `/api/release`. When `api.sql` is true, read `/api/schema?format=sql` and use SQL for joins, inventories, counts and comparisons. Select the evidence fields needed for the answer, including IDs and source URLs; avoid fetching one whole initiative at a time. Use the descriptions to interpret relationships and dates. Check truncation, and correct queries using returned SQL errors. Otherwise use the directory and detail views and complete relevant result pages.

## Answer from evidence

- Cite original source URLs or DOIs for key claims. Read records and source statements beyond search excerpts; show conflicting statements and unresolved matches when they affect the answer.
- Distinguish commitments from delivered outputs, a person's role from their Node's obligation, and a resource listing from explicit endorsement. State funding or in-kind status only where a source says it. Do not infer staff effort from roles.
- For activity or progress, use dated events, outputs and statements. Retrieval dates are not activity dates. Report the latest evidence and coverage limits; missing public evidence does not establish inactivity or a capability gap.
- Fit the answer to the requested task: contacts and overlaps, commitments and reporting, resources grouped by type, or roadmap and handover material. Label proposed activities as proposals and identify missing evidence instead of filling gaps with assumptions.
