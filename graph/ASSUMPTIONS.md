# Assumptions and open questions

Decisions agreed with the project owner on 2026-11-10, and the defaults the build applies where a question stays open.

## Scope

- Product: one internal SQLite database (`graph/build/graph.sqlite`) plus `schema_config.yaml` (descriptions of every table and column), `run.json` and `provenance.json`. It contains Perun personal data, so it is internal only and never committed (`build/` is git-ignored).
- Stories 4, 6, 7 and 8 are the target; story 5 (induction) is served only by group contacts and people's roles.
- Sources: ELIXIR website pages about groups, projects, Nodes and EU projects; Node websites (team, people and project pages); Commissioned Service and Platform work plans on Zenodo (including records 17633187, 19469586, 12516053, 12807532, 16993903); STEERS and CONVERGE handbooks; CORDIS fact sheets of STEERS, CONVERGE, EXCELERATE; the Scientific Programme 2024-28, Annual Report 2025 and Systems Biology Community documents; Zenodo record metadata; F1000 Gateway item metadata; bio.tools; TeSS; Europe PMC systems biology reviews; Perun.
- Left out: F1000 poster and slide full texts, deliverable PDF full texts (their Zenodo metadata is in), ELITMa modules, de.NBI service and training pages, news and event archives, documents that need permission.
- `scripts/catalogues.py` turns the paginated JSON API dumps (bio.tools, TeSS, Zenodo, Europe PMC) and F1000 landing-page metadata into one JSONL table per catalogue in `data/extracted/catalogues/` (git-ignored, reproducible). Biotope would otherwise describe every API page as its own source.
- `scripts/documents.py` lists the documents the extractions read; each is registered as a single-file dataset.

## Extraction

- Language-model extraction uses `openai/gpt-6.1-terra` on OpenRouter with low reasoning effort, on public documents only. Perun data is never sent.
- Code reads structure first (main page content, PDF pages, CORDIS tables); the model reads only the cleaned text. Every record carries a verbatim quote, checked against the document.
- EDAM topics for groups, projects and plan items are assigned by the model from the 296 EDAM topics bio.tools and TeSS use (`graph/extraction/edam_topics.json`). They are interpretations, marked as model-assigned.

## Identity

- People are joined on a shared ORCID iD or a shared email only when their names are compatible (equal, a known variant, or one name's words contained in the other's); a shared address with an incompatible name is a `person_match` review item instead, unless the names share no word (a group mailbox). Perun accounts with the same email are one person. The same full name (case, accents, punctuation and titles ignored; "Surname, Given" read as "Given Surname") joins only when no two ORCID iDs or Perun accounts carry it. Spelling variants ("Alex"/"Alexander", a dropped middle name or particle, reversed name order) are not joined; each pair is an open `person_match` review item.
- Emails are used for matching only; the export keeps people's email domains, never their addresses, and role evidence quotes show "[email]" instead. Contact addresses that group pages publish stay in `contacts`, and catalogue descriptions (TeSS, Zenodo) are kept as published. Partner codes ("UiB-WP3"), organisation names and generic words ("Chairs", "Helpdesk") are not people.
- ELIXIR Nodes come from a closed list with aliases (country names, `ELIXIR-XX` codes, Node brands such as de.NBI, BioData.pt, IFB, INB, NBIS). Organisations such as SIB or CSC are not read as Nodes.
- Groups and projects are joined, in this order, on:
  1. the same page URL (after redirects; a CORDIS project's "results" and "reporting" pages are its fact sheet);
  2. a curated alias (`CURATED_ALIASES` in `alignment/initiatives.py`: each Platform's two 2024-26 Commissioned Service pages, the two URLs of the CMR, HDTR and BFSP Scientific Programme area pages, and the BFSP work plan record);
  3. the same Scientific Programme code ("2024-TECHNOLOGY-Data", "24-SCIENCE-BFSP"), when a project's name, acronym or own page carries it;
  4. a work-package or EU-project sub-page joining its parent page;
  5. a document (Zenodo record or PDF) that exactly one project page links;
  6. a listing that links a page, when both are groups or both are projects and they share a name word other than ELIXIR, Platform, Community or Group;
  7. the same name after ignoring case, "ELIXIR", the words Community/Platform/Focus Group/Group and a bracketed acronym;
  8. for projects only, the same acronym (at least four characters, also read from a bracket such as "(BFSP)"), and the title part before a colon; a trailing "programme" is ignored;
  9. a reviewer's `same` decision.
- Communities and Platforms are matched only within their kind; other groups (focus groups, working groups, task forces, governance groups) share one name space. Rules 3 and 5 to 8 never join two pages of one website whose last path segments differ; Zenodo records, PDFs and F1000 items are exempt. Other likely matches are open `initiative_match` review items.
- A Platform and its 2024-26 Commissioned Service are separate initiatives; the service's `related_to` edges point to the Platform. The Platform work plans on Zenodo belong to the service.
- The main page is the ELIXIR website's page, preferring a Scientific Programme page over an `internal-projects` page; its name and dates win. Initiative ids come from the last path segment of the shortest ELIXIR page (`initiative:data`), then from the other pages, then from the full path, and only then from the name.
- Plan items whose owner is ELIXIR as a whole belong to `initiative:elixir` (kind infrastructure).
- Node websites' own groups are `node_group`; a Node's own work programme is `node_programme`; ELIXIR-wide services and resources are `infrastructure`.
- A group or project that only role statements or plan items name becomes its own initiative, with a kind guessed from its name. Bodies without "ELIXIR" in their name (General Assembly, boards, committees, councils, SAB, PMT) in a document that describes a project are the project's, recorded as the role's `work_item`, not as separate groups. On a Node's website such a body is the Node's own (`node_group`, named with the Node), never the ELIXIR-wide body of that name. A role is placed on the group or project the document describes when the stated place is a subset of its names, and a work-package role on the sub-project that its work item names by acronym ("Work Package 3, DBTLHub").
- Work packages, tasks, deliverables and milestones belong to the project that their document describes (a Platform work plan's WPs belong to the work plan's Commissioned Service, not to the Platform), or to the sub-project their owner names by acronym. Task codes keep their dots (T2.1 is not T21); generic codes ("Activity 1", "Goal 2") are scoped by their parent.
- When sources label one plan item differently, a list entry that starts with the code wins over a mention in running text; mentions whose label shares no word with it are set aside (counted as `plan_mentions_set_aside`).
- Organisations are joined on equal names after ignoring case, punctuation and a leading CORDIS country code ("CH-SIB" is "SIB"); likely matches are `organisation_match` review items.
- When several snapshots of one page (the same final URL) were extracted, only the newest is used (policy `superseded_snapshot`).

## Roles

- ELIXIR Hub staff named in a group are recorded with `role_kind` liaison unless the source gives them a lead or chair title.
- When an EU project's web page names more than three leads for the same task, they are recorded as participant (the STEERS and CONVERGE pages list every partner under a task's "Leadership").
- Members of a Node's advisory board are not placed in that Node.
- `funding` is funded or in_kind only when the role's evidence quote speaks of funding; otherwise `not_stated`.

## Outputs

- A Zenodo record delivers a deliverable when a plan item links it, or when its title carries the deliverable's code and either the record names the project's EU grant or the title repeats the deliverable's label.
- A keyword links an output to a group only when it names a Community, Platform, Focus Group or ELIXIR group; title acronyms link to projects with that acronym (basis `named`, the weakest).

## Conflicts

- Each source's statement about a group or project is kept as a `source_statement`. Dates more than a month apart, different work package or task leads, a person's Node differing between sources, and Nodes that one source lists and another omits are `value_conflict` review items. The number of Nodes is not taken from text; it is counted from `takes_part_in` edges.
- A year-only date covers the whole year, so "2024" agrees with "2024-03".
- An initiative's start and end come from its main page when that page states them, even when other sources disagree (the disagreement is still a review item). Otherwise they come from the sources that agree, and are null while sources disagree.
- Plan-item dates written as project months ("M36") become calendar months only when the project's start month is known.

## Review decisions

- Reviewers write decisions to `data/input/review-decisions.csv` (columns `review_id`, `decision`), described in its annotation file. For match items the decision is `same` or `different`; for value conflicts it is the correct value (a date for start, end and date conflicts, which the build then uses) or `all valid`.
- Each build applies the decisions and exports those items with status `resolved` and the decision, so they do not come back as open. `run.json` counts the decisions applied.
- A review id derives from its subjects' ids and the property. If new data changes those ids, the old decision no longer matches and the item shows as open again.

## Funding and time

- An organisation's EU contribution (CORDIS) is never read as a person's funding. A person's work is funded or in-kind only where a source states it; otherwise `not_stated`.
- Time spent in roles is recorded only where a source states it (rare); otherwise null.

## Known gaps

- Person variants (a nickname, a dropped middle name, several Perun accounts with one name) stay separate records with open `person_match` items; some people therefore appear 2–4 times until reviewed.
- `related_to` does not say whether a link is formal participation or a mention.
- Stated counts ("seven Nodes"), documents that need permission and page publication dates are not stored.
- Roles from older handbook versions are kept beside newer ones; `period` is rarely stated.
- 45% of role holders have no Node, because organisations are not linked to Nodes.
- One BFSP listing ("Biodiversity, food security and pathogens") stays a separate row beside `initiative:bfsp`.

## Open questions

- The Perun export (1,622 accounts) does not record which Perun group it comes from; it is used as a list of known people only.
- TeSS Node and collection names are matched to TeSS's numeric IDs by equal counts in the TeSS facets; an ID whose count is not unique stays unnamed, so TeSS links to Nodes and groups are incomplete. The snapshot has no TeSS node or collection list that would name them all.
- Organisations are not linked to Nodes; `organisation.country` (from CORDIS) can be joined with `elixir_node.country`, which shows location, not Node membership.
