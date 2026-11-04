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
