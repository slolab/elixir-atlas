# Data sources

Collection results and source URLs: [scraping index](../data-sources-scraping.jsonl).
See [coverage and scraping instructions](data-sources-scraping.md).

## Public

1. **ELIXIR website** (stories 3, 4, 5)
   - Why: Platforms, Communities, Nodes, Focus Groups, their leads and members; current news and event listings.
   - How: save pages from [elixir-europe.org](https://elixir-europe.org) with Playwright, loading saved cookies and pausing for manual bot checks when needed.
   - Scope: latest news listing only; no news articles or archive pagination. Relevant events linked from core pages and explicitly named sources remain included.
2. **ELIXIR Scientific Programme** (stories 1, 3, 6)
   - Why: official goals and tasks of each Platform and Community.
   - How: [2024–28 full Programme PDF](https://elixir-europe.org/sites/default/files/documents/elixir-programme-24-28-full.pdf), linked from the [Scientific Programme page](https://elixir-europe.org/how-we-work/scientific-programme).
3. **Node websites** (stories 1, 2, 4, 5)
   - Why: what each Node does and who works there; evidence for comparing Node strengths, gaps and activities.
   - How: save public pages and linked documents from [ELIXIR UK](https://elixiruknode.org/), [ELIXIR Germany / de.NBI](https://www.denbi.de/) and [ELIXIR Spain / INB](https://inb-elixir.es/), including people, services, projects and current listings. Keep only the latest news listing; exclude job postings and old website event/training archives. Job searches are not among the current DOCX user stories.
   - Scope: start with these three Nodes, which include contributor countries. UK remains a worked example, not a restriction; extend the list as more Nodes are added.
4. **ELIXIR Communities Handbook** (stories 4, 5, 6)
   - Why: what a Community is, its structure, the roles of leads and members.
   - How: [Communities Handbook 2024 on F1000Research](https://f1000research.com/documents/13-80), including its PDF.
5. **People and Nodes onboarding videos and documents** (story 5)
   - Why: induction to ELIXIR roles, Nodes and the Hub.
   - How: start with the [PeoplePulse onboarding protocol](https://zenodo.org/records/17202558) and records linked from the ELIXIR site. Download documents; keep video links for later processing.
6. **ELITMa modules** (story 5)
   - Why: management training for Node staff: governance, data management strategy, leading teams.
   - How: [ELITMa](https://elixir-europe-training.github.io/ELIXIR-ELITMa/).
   - Scope: collect the available module pages, including placeholders, for later review.
7. **"Demystifying ELIXIR" Hub event** (stories 3, 5)
   - Why: overview of ELIXIR for newcomers.
   - How: slide deck linked from the [event page](https://elixir-europe.org/events/demystifying-elixir-everything-you-ever-wanted-know-and-more).
8. **ELIXIR publications** (stories 1, 2, 3, 5)
   - Why: positions, outputs and authors by topic.
   - How: [F1000Research ELIXIR Gateway](https://f1000research.com/gateways/elixir) (documents, articles, posters, slides) and Zenodo.
9. **Systems Biology Community publications** (stories 3, 6)
   - Why: outputs and positions of one Community, as the worked example.
   - How: [event report](https://f1000research.com/documents/15-1717), [opinion article](https://doi.org/10.12688/f1000research.126734.2), [arXiv paper](https://doi.org/10.48550/arXiv.2609.13127).
10. **bio.tools** (stories 1, 2, 6)
    - Why: tools and services, with their ELIXIR Node, Platform and Community.
    - How: [API](https://bio.tools/api/t/?format=json).
11. **TeSS** (stories 1, 2, 5, 6)
    - Why: training events and materials by Node and topic.
    - How: full JSON-API catalogues for [events, including past events](https://tess.elixir-europe.org/events.json_api?include_expired=true) and [materials](https://tess.elixir-europe.org/materials.json_api), following pagination. These are catalogue records, not downloads of every external training website.
12. **FAIRsharing** (stories 2, 6)
    - Why: standards, databases and policies ELIXIR recommends.
    - How: [fairsharing.org](https://fairsharing.org); the API needs a free account.

## Needs permission

13. **Systems Biology Community monthly minutes (2025+)** (stories 1, 2, 4, 5)
    - Why: plans, decisions, who is active, overlap with other groups.
    - How: [Google Doc](https://docs.google.com/document/d/1BdJVO_5W3bywl8L5mLu66jRbZmjiWIPTsRjD6kNuejo/edit?usp=sharing); Carissa to check.
14. **Systems Biology Community F2F 2026 documents** (stories 4, 6)
    - Why: plans, people and topics of one Community.
    - How: [agenda](https://docs.google.com/document/d/1dMFnvVqOC9leNQ-switvz_d_9CZoglM7ePXhKHBZBBE/edit?usp=sharing), [slides](https://docs.google.com/presentation/d/1o9G6B3LoJrht1mIGAf6mzbdIgyI0LAEarpjkR5LQzWE/edit?usp=sharing).
15. **Node Commissioned Service project: WP deliverable on Node structure** (stories 1, 5)
    - Why: how Nodes are structured, governed and run events.
    - How: Xenia, if permission is granted.
16. **Archived Commissioned Services project plans** (stories 2, 4)
    - Why: deliverables and people per project (budget redacted); stands in for prior grant applications.
    - How: Xenia, if permission is granted.

## Extended stories — 10 November 2026

17. **CORDIS: STEERS, CONVERGE and EXCELERATE** — public
    - Why: project dates, participating organisations, funding, reports and deliverables for grant writing, contributions and webpage updates.
    - How: English fact sheets, results and reporting pages for grants [101131096](https://cordis.europa.eu/project/id/101131096), [871075](https://cordis.europa.eu/project/id/871075) and [676559](https://cordis.europa.eu/project/id/676559), including public attachments. Organisation funding does not establish individual funding.
18. **Project outputs and example pages** — public
    - How: Zenodo searches by those three grant numbers, plus the STEERS community, including all record versions. Retain metadata and document/office attachments; exclude bulk CSV/TSV/JSON/XML research data. Explicit 24-compute and FAIR-FEGA pages retain conflicting evidence and support later comparisons. These commissioned activities have no identified Zenodo collection.
19. **Additional Node teams and plans** — public
    - How: bounded official pages for Czechia, Finland, Luxembourg, Netherlands, France, Norway, Portugal and Switzerland, named in the example projects. Exact URLs and path boundaries are in `sources.py`.
    - Scope: teams, projects and roadmaps; Switzerland includes the first group listing and a named 24-compute participant lookup, rendered in Chrome. One explicit Portuguese FAIR-FEGA announcement supplies named contributions; other news remains excluded. Public profiles do not establish actual effort or complete membership.
20. **Europe PMC: Systems Biology reviews** — public
    - Why: an external baseline for the Community's state-of-the-art question.
    - How: JSON metadata and abstracts for reviews matching “systems biology” in title/abstract, published 2022–10 November 2026. No full-text crawl; the query is explicit in `sources.py`.
21. **Project participation records** — needs permission
    - Need: approved task assignments, person/Node links, funded/in-kind status and effort for STEERS, 24-compute and FAIR-FEGA. Preserve unknown values; do not infer them from organisation funding.
22. **Group membership and activity** — needs permission
    - Need: approved rosters, work plans, minutes and participation summaries for Communities, Platforms, Focus Groups, working groups and task forces. Link-accessible Drive documents remain restricted unless approved for public use.
23. **Bid outcomes** — needs permission
    - Need: approved redacted application records and outcomes, including unsuccessful bids; public funded-project catalogues cannot supply these.

## Manually supplied

**Perun people database**: two user-provided CSV exports in `data/input/perun/`, included in the S3 snapshot at the user's request. Treat them as restricted: they contain names, affiliations, email addresses and account identifiers. Keep the original exports unchanged; their contents are not committed to Git or approved for public output.
