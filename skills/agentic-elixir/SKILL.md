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
4. Check `/api/release`. When `api.sql` is true, discover tables with `/api/schema?format=sql&detail=summary`, then request full definitions for the tables you need. Fetch candidate facts and their supporting evidence together with batched SQL joins and projections, including IDs and source URLs. Avoid fetching one whole initiative or relationship at a time; use individual record views for unresolved details. Check truncation and correct queries from returned errors. Otherwise use directory/detail views and complete relevant result pages.
5. Establish the requested population before counting or claiming absence. National groups and pan-ELIXIR Communities can share a kind; a null status means unstated, not ended. Check source directory statements and canonical pages, and keep uncertain inclusion explicit.

## Answer from evidence

- Verify each requested claim against source statements, relationship evidence and plan items. Before answering, check that each requested field is supported or explicitly unavailable. Aggregated contacts, dates and roles can combine different sources or subgroups. Preserve source wording such as co-lead, interim, planned and reported; compare conflicting statements instead of relying only on the merged value. Cite original URLs or DOIs.
- Distinguish commitments from delivered outputs, a person's role from their Node's obligation, and a resource listing from explicit endorsement. State funding or in-kind status only where a source says it. Do not infer staff effort from roles.
- For activity or progress, use dated events, outputs and statements. Retrieval dates are not activity dates. Search for named mentions in outputs, related projects and statements as well as direct links; missing graph edges do not establish absence. Report the latest evidence and coverage limits; missing public evidence does not establish inactivity or a capability gap.
- Fit the answer to the requested task: contacts and overlaps, commitments and reporting, resources grouped by type, or roadmap and handover material. Label proposed activities as proposals and identify missing evidence instead of filling gaps with assumptions.
