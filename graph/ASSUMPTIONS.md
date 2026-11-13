# Assumptions and open questions

Decisions agreed with the project owner on 2026-11-10 and 2026-11-11, and the defaults the build applies where a question stays open.

## Scope

- Product: one SQLite database (`graph/build/graph.sqlite`) plus `schema_config.yaml` (descriptions of every table and column), `run.json` and `provenance.json`, never committed (`build/` is git-ignored). Perun data stays in the build and in the public release; the owner decided this on 2026-11-11.
- The snapshot is a crawl of public pages and catalogues. Absence from it, or no recent page, does not show that a group or person is inactive. Community member lists are not public; the people of a group are those public pages name.
- Stories 4, 6, 7 and 8 are the target; story 5 (induction) is served only by group contacts and people's roles.
- Sources: ELIXIR website pages about groups, projects, Nodes and EU projects; Node websites (team, people and project pages); Commissioned Service and Platform work plans on Zenodo (including records 17633187, 19469586, 12516053, 12807532, 16993903); STEERS and CONVERGE handbooks; CORDIS fact sheets of STEERS, CONVERGE, EXCELERATE; the Scientific Programme 2024-28, Annual Report 2025 and Systems Biology Community documents; Zenodo record metadata; F1000 Gateway item metadata; bio.tools; TeSS; Europe PMC systems biology reviews; Perun.
- Also read since 2026-11-11: the Systems Biology preprint (2609.13127), the Community papers on F1000 (Galaxy, Single-Cell Omics, Toxicology, Domestic Animals, Plant Sciences meeting reports, the Communities Handbook), the RDM Community framework, the STEERS milestone and deliverable PDFs, all ELIXIR-UK project pages, the de.NBI commissioned services list, the rare-disease service bundle, the ELIXIR events listing and event pages, and the three bio.tools domains the Systems Biology page links.
- Left out: F1000 poster and slide full texts, ELITMa modules, de.NBI training pages, news archives, documents that need permission.
- `scripts/catalogues.py` turns the paginated JSON API dumps (bio.tools, TeSS, Zenodo, Europe PMC) and F1000 landing-page metadata into one JSONL table per catalogue in `data/extracted/catalogues/` (git-ignored, reproducible). Biotope would otherwise describe every API page as its own source.
- `scripts/documents.py` lists the documents the extractions read; each is registered as a single-file dataset.

## Extraction

- Language-model extraction uses `openai/gpt-6.1-terra` on OpenRouter with low reasoning effort, on public documents only. Perun data is never sent.
- Code reads structure first (main page content, PDF pages, CORDIS tables); the model reads only the cleaned text. Every record carries a verbatim quote, checked against the document.
- Facts that ELIXIR pages state in their structure are read by code, not the model (`extraction/elixir_pages.py`): the directory of Communities, Platforms and Focus Groups with current or past status and transitions, page dates, contact links, the join button and its text, the co-lead election candidates, and the events listing. The model's role statements from the election page are replaced by the parsed candidates (policy `superseded_by_page_parser`).
- Recommendations (`extraction/recommendations.py`) are read by the model from Community pages and Community papers: one record per resource and group, with kind, basis (recommends, develops, lists), purpose and link.
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
- The ELIXIR directory pages (/communities, /platforms, /focus-groups and the archived Marine Metagenomics page) are the registry of Communities, Platforms and Focus Groups. Each entry is its own initiative, named from the directory, with status current or past; two entries never join. A past Focus Group whose page now redirects to its Community stays a separate initiative. Any other group that sources call a community, platform or focus group is `node_group` when only Node websites name it, else `other_group`. `became` edges come from the directory's transition sentences.
- Commissioned Services, Implementation Studies and Scientific Programme projects are one kind, `commissioned_service`; `programme` is set for projects with a page under /how-we-work/scientific-programme.
- Node websites' own groups are `node_group`; a Node's own work programme is `node_programme`; ELIXIR-wide services and resources are `infrastructure`.
- A group or project that only role statements or plan items name becomes its own initiative, with a kind guessed from its name. Bodies without "ELIXIR" in their name (General Assembly, boards, committees, councils, SAB, PMT) in a document that describes a project are the project's, recorded as the role's `work_item`, not as separate groups. On a Node's website such a body is the Node's own (`node_group`, named with the Node), never the ELIXIR-wide body of that name. A role is placed on the group or project the document describes when the stated place is a subset of its names, and a work-package role on the sub-project that its work item names by acronym ("Work Package 3, DBTLHub").
- Work packages, tasks, deliverables and milestones belong to the project that their document describes (a Platform work plan's WPs belong to the work plan's Commissioned Service, not to the Platform), or to the sub-project their owner names by acronym. In a programme work plan (BFSP), a work package whose label starts with a project's name or acronym ("Odyssey: ...") takes its deliverables, milestones and tasks of the same number to that project. Task codes keep their dots (T2.1 is not T21); generic codes ("Activity 1", "Goal 2") are scoped by their parent.
- When sources label one plan item differently, a list entry that starts with the code wins over a mention in running text; mentions whose label shares no word with it are set aside (counted as `plan_mentions_set_aside`).
- Organisations are joined on equal names after ignoring case, punctuation and a leading CORDIS country code ("CH-SIB" is "SIB"); likely matches are `organisation_match` review items.
- When several snapshots of one page (the same final URL) were extracted, only the newest is used (policy `superseded_snapshot`).

## Roles

- ELIXIR Hub staff named in a group are recorded with `role_kind` liaison unless the source gives them a lead or chair title.
- When an EU project's web page names more than three leads for the same task, they are recorded as participant (the STEERS and CONVERGE pages list every partner under a task's "Leadership"). The same applies to plan items that list more than three people as leads.
- People work on plan items as `lead` or `participant` (`works_on_plan_item`); names come from role statements and from the plan items' lead and participant lists, including names in brackets after a partner code ("EE-UTAR (Priit Adler)").
- Co-lead election candidates are `holds_role` edges with `role_kind` candidate and the election year as period; they hold no office yet.
- A lead, co-lead or coordinator of a Community, Platform or Focus Group named on its own ELIXIR page adds a `takes_part_in` edge from their Node (not the Hub) with basis `lead_node`; Node lists give basis `stated`.
- Contacts are the addresses a group's own ELIXIR page shows. When a contact link sends to another address than it shows, the shown one is kept and a `value_conflict` review item (property contact) names both.
- Members of a Node's advisory board are not placed in that Node.
- `funding` is funded or in_kind only when the role's evidence quote speaks of funding; otherwise `not_stated`.

## Outputs

- A Zenodo record delivers a deliverable when a plan item links it, or when its title carries the deliverable's code and either the record names the project's EU grant or the title repeats the deliverable's label.
- A keyword links an output to a group only when it names a Community, Platform, Focus Group or ELIXIR group (basis `named`). A title acronym links to the project with that acronym, and a title that names a directory group ("Galaxy Community", "ELIXIR Compute Platform") to that group (basis `title`). A description that names a directory group links with basis `description`, the weakest. Platform names count only after "ELIXIR".
- A deliverable code in a title matches another project's deliverable only when the output is already linked to that project.
- F1000 items with the same DOI are one output (policy `duplicate_record`). Zenodo contributors are authors after the creators.

## Tools, resources and events

- A bio.tools entry is in when it has an ELIXIR tag, is in a bio.tools domain the Systems Biology page links (`tool_for` basis `community_domain`), credits a person whose full name a role statement, plan item or election page gives, or is the bio.tools entry of a tool or database a group recommends.
- A resource is one per name after ignoring case and punctuation; `is_tool` links it to a bio.tools entry with the same link or the same unique name. A recommendation counts only when its group matches a directory group.
- ELIXIR website events are `event` nodes with `listed_in` elixir_website, linked to groups their title names; TeSS events keep the TeSS entry as `url`, the organiser's page as `provider_url`, and the collection page as the link's `source_url`.

## Conflicts

- Each source's statement about a group or project is kept as a `source_statement`. Dates more than a month apart, different work package or task leads, a person's Node differing between sources, and Nodes that one source lists and another omits are `value_conflict` review items. The number of Nodes is not taken from text; it is counted from `takes_part_in` edges.
- A year-only date covers the whole year, so "2024" agrees with "2024-03". A year-only end date is compared as December, so "through 2026" conflicts with "January 2026".
- `planned` status is kept only for initiatives that start after November 2026.
- An initiative's start and end come from its main page when that page states them, even when other sources disagree (the disagreement is still a review item). Otherwise they come from the sources that agree, and are null while sources disagree.
- Plan-item dates written as project months ("M36") become calendar months only when the project's start month is known.

## Review decisions

- Reviewers write decisions to `data/input/review-decisions.csv` (columns `review_id`, `decision`), described in its annotation file. For match items the decision is `same` or `different`; for value conflicts it is the correct value (a date for start, end and date conflicts, which the build then uses) or `all valid`.
- Each build applies the decisions and exports those items with status `resolved` and the decision, so they do not come back as open. `run.json` counts the decisions applied.
- A review id derives from its subjects' ids and the property. If new data changes those ids, the old decision no longer matches and the item shows as open again.

## Funding and time

- An organisation's EU contribution (CORDIS) is never read as a person's funding. A person's work is funded or in-kind only where a source states it; otherwise `not_stated`.
- Time spent in roles is recorded only where a source states it (rare); otherwise null.

## Build v3 rules

Each rule applies to a whole class of records. The CQs of `eval/cqs/atlas_261111` that exposed the problem are in brackets; see `docs/eval-analysis-2026-11-12.md`.

- Each extraction keeps its own newest snapshot of a page. A newer snapshot that only another extraction read no longer drops older records (015, 016).
- An initiative's own page is its ELIXIR page: scientific-programme or directory pages first, then internal-projects pages, then Node and other sites. Its kind is the kind its own page states; dates follow the existing own-page rule (006, 013, 014).
- Pages of a Scientific Programme area (`/science/<area>`) are kind `programme_area`, not projects (020).
- A role of kind `lead` on a Community, without a work item, is a co-lead: Communities are led by co-leads (018).
- A plan item's lead list naming more than three people is a membership list. It moves to `participants`, and the real leads come from task-leader statements (007, 008).
- `period_status` derives ended, running or not_started from the dates at the snapshot date (012, 014).
- `related_to` is stored in both directions (001, 018, 020).
- `takes_part_in` basis `own_page` marks Node lists on the initiative's own main page; `stated` marks other sources (013, 014).
- A Zenodo record names a grant as `output_of` only when it is dated no later than the year after the project ended (013).
- `recommends` has two bases: `develops`, and `recommends` for every other pointer from the group's own documents, so an agent cannot read a listing as weaker than a recommendation. A resource whose URL is a bio.tools entry or a tool's homepage links to the tool whatever its kind (015).
- `joining` keeps each link's URL in brackets (004).
- A group enumeration such as "the A, B and C Communities" names each group, not only the last one (002).
- F1000 items take their abstract as description, and a group listed as an author links the output with basis `author` (002).
- EU projects link to a Node with basis `beneficiary_country` when a CORDIS beneficiary is in the Node's country (006, 013, 014).
- A Zenodo output whose title starts like other outputs of one work-package series ("<name> CoS | WPn |") joins the one project the other outputs of that series belong to, with basis `series` (013).
- Events and training materials list the TeSS collections they appear in (`collections`, plus a count of unnamed ones), so "in a group's collection" and "only in TeSS" can be told apart (017).
- When no output of a series is linked, the series takes the project that the work plan explaining its other work packages assigns to that work package (013).
- A work package whose title is the name of a project, with or without a colon, places its plan items on that project (013).
- A Zenodo grant string that is not a CORDIS grant, such as "2023-COMM-<acronym>", links the output to the one project with that acronym, with basis `grant` (013).
- Zenodo contributors are kept apart from creators: `authored.role` is `creator` or `contributor`, and `output.contributors` lists them (013, 021).
- `node_involved_in.node_site` says whether the Node's own website names the initiative. `not_listed` is set only for Nodes whose project listing was collected: ELIXIR-UK, de.NBI, ELIXIR CZ, Luxembourg, the Netherlands and Norway (013, 014).
- A plan item that names a bio.tools tool, by name or by the long name its bio.tools description gives, lists it in `tools` with the people bio.tools credits, when the item's initiative tags or recommends the tool or one of its people is credited for it (019, 021).
- A plan participant whose name is an initiative or Node name is not a person (019).
- A plan, page or report that links its work to another project's work gives a `plan_linked_to` edge, in both directions, with the work items and the quote. An LLM extraction (`plan_links`) reads project pages, work plans, handbooks, Community papers and EU project documents that cite a work item code (010).

### Precomputed records

The build gathers the joins that most questions need, so one row answers them. The rules are the same for every initiative, person and Node.

- `involved_in`: one row per person and initiative with every role, plan item, authored output (not by description) and every bio.tools tool credited to the person, marked when the initiative tags or recommends it. `leadership` is true for a leadership role or a plan item the person leads (005, 008, 018, 019, 021).
- `node_involved_in`: one row per Node and initiative, from Node lists, EU beneficiaries in its country, lead Nodes and its people's roles or plan items. It lists the plan items the Node or its people lead and work on, and counts them against the initiative's plan items, so "leads none" is stated (006, 007, 008, 013, 014).
- `shares_work_with`: two groups linked to the same project, output, tool, leader (not liaison) or resource. Items shared by more than eight groups, programme areas and ELIXIR-wide projects are left out (001, 018, 020).
- Initiative fields: `leaders`; `limits`, from the kind and data, including the registrar group a join button leads to and an end date passed with no completion stated (003, 004, 012); `recent_activity` with `latest_own_activity` and `latest_activity`; `scope`, the outcomes, goal labels, resources and tools as search text (002, 018). `Tool.recommended_by` lists the groups whose documents point to it (015).
- The API views list these records and add no logic of their own.

## Build v4 rules

From the ELIXIR-UK COG form check (Xènia) and the website-content review (Debbie) of release `20261112`. Each finding was traced to a class of records; the rules below fix the class, and `data/input/corrections.csv` holds what no public page states.

### Extraction

- The HTML cleaner no longer drops elements whose class names a sidebar. The ELIXIR-UK theme puts all page content in `aside#sidebar`, so the model never saw the "governance roles" of 122 UK people pages, the "Coordination / leads" of 14 activity pages or 26 ORCID links (Haerty, Loach). Menus and breadcrumbs are still dropped.
- ELIXIR-UK people and activity pages are read by code (`extraction/node_pages.py`, extraction `node_page_roles`), not by the model: title, organisation, ORCID, governance roles, the groups a person leads ("Community leadership"), the groups, clubs and projects on the profile, and an activity page's coordination/leads. A person is placed in ELIXIR-UK only when their organisation is listed as a UK member (`/members/`); external advisers stay without a Node. Each record's evidence quote is the page block it was read from, rendered like the document text (links inline), so it is verbatim in the document.
- Role extraction checks recall against the page's own links: people the page links to a profile (`/users/…`, `/people/…`) but no record names get a second ask that lists them. Names match on folded letters, and on the same surname with one given name a prefix of the other (Alex/Alexander).
- Work plan PDFs have no links to check against, and a full re-run dropped whole "WP Partnership" lists (17 Interoperability Platform members; the BioDiv-FAIR-Checker WP 6 lead in the BFSP plan) that the earlier run had. The instructions now name that list form, and those plans were redone.
- `scripts/extraction_check.py` scores the extraction against `eval/extraction/fixtures.yaml` (expected and forbidden facts from the feedback cases and the work plans) and reports, over all role documents, person links lost in cleaning, linked people with no record, pages with no records, and people a document had in the committed extraction but no longer has.

### Precedence and corrections

- `data/input/corrections.csv` is tier 0: a Node-confirmed `node` (add/remove), `role` (add/remove) or `kind` (set) for an Atlas id. It wins over every source, applies before leaders, Node involvement and kinds are derived, and a correction whose subject or target is missing is excluded as `correction_target_missing` in `run.json`. Seeded with the 8 COG findings.
- Current leaders of a Community, Platform or Focus Group come from its own ELIXIR page when that page lists leads. A lead, co-lead, chair or coordinator that only another page names (a Node website, a past page) is `unconfirmed_lead` and raises a `value_conflict` review (property `leader`) instead of counting as leadership.
- A person's current Nodes leave out a Node that only the own page of a past group states when a current source gives another (Emily Clark: past Focus Group page says UK, current Community page says EMBL-EBI). `InNode` keeps every statement. An email domain whose country Node differs from a member-Node-only placement raises a `value_conflict` (property `node`).
- A bio.tools credit alone no longer makes an `involved_in` row; it only adds tools to an involvement that rests on a role, plan item, authored output or correction (Wendi Bacon and Galaxy through TIaaS).

### Identity, kinds and plans

- EU projects: a trailing year range ("(2022–2027)"), "European" and "project" are ignored in the name key, and acronyms of three letters join when both claims are EU projects (GDI). Differing ranges become date conflicts.
- A Node project page joins the ELIXIR project page with the same hyphenated last path segment (`elixiruknode.org/project/2022-edp2`).
- A listed project whose name matches a Scientific Programme area's name, ignoring ELIXIR, years and "priority area / work plan / programme", joins the area (the BFSP listing).
- Person names with three or more words join a person with the same words in another order ("Pérez Sitjà Xènia"). Names containing the legal form "ERIC" are organisations.
- A project on ELIXIR's EU projects page or in CORDIS is `eu_project`, whatever its own page says (EOSC-ENTRUST).
- Project months ("M26") count from the earliest start among the projects the stating document describes, not from the sub-project the item is moved to (BFSP WP6 items moved to BioDiv-FAIR-Checker).
- A plan item that an output delivers has status `delivered`.
- `part_of` links a sub-project or sub-group to its parent: basis `sub_page` (its own page sits under the parent's page) or `work_plan` (a programme work plan has a work package for it).

## Known gaps

- Person variants (a nickname, a dropped middle name, several Perun accounts with one name) stay separate records with open `person_match` items; some people therefore appear 2–4 times until reviewed.
- `related_to` does not say whether a link is formal participation or a mention.
- Stated counts ("seven Nodes") and documents that need permission are not stored.
- Roles from older handbook versions are kept beside newer ones; `period` is rarely stated.
- 45% of role holders have no Node, because organisations are not linked to Nodes.
- Facts no public page states (membership known only to the Node or in Perun groups) enter only through `corrections.csv`; the Perun export has no group column.
- An `output` plan item that a Zenodo link creates stays beside the coded milestone the same record delivers.
- Some UK Node pages about an ELIXIR group join that group even when they describe its earlier form (the UK Cancer Data Focus Group page joins the Cancer Data Community).
- Long work plans still lose some partner-list members between runs (in v4 the 83-page BFSP plan lacks 4 of about 100 people the previous run had). Re-runs vary: the fixtures and the drop report in `scripts/extraction_check.py` show it, but they do not fix it.

## Open questions

- The Perun export (1,622 accounts) does not record which Perun group it comes from; it is used as a list of known people only.
- TeSS Node and collection names are matched to TeSS's numeric IDs by equal counts in the TeSS facets; an ID whose count is not unique stays unnamed, so TeSS links to Nodes and groups are incomplete. The snapshot has no TeSS node or collection list that would name them all.
- Organisations are not linked to Nodes; `organisation.country` (from CORDIS) can be joined with `elixir_node.country`, which shows location, not Node membership.
