# Scraping

## Original collection — 4 November 2026

The full run and Germany's resumed traversal finished. All source queues are empty; coverage still has the gaps below. `data/input/` contains **5,651 files, 3.39 GB**. Saved paths and sizes are verified. Historical responses, versions and aliases remain included.

| Source | Collected | Coverage / gap |
| --- | --- | --- |
| ELIXIR and UK, German, Spanish Nodes | 1,241 / 544 / 706 / 15 saved URLs: people, services, projects and documents. | Configured links traversed; broken, private, blocked and robots-disallowed URLs remain. Site-wide completeness is unverified. |
| Strategy and induction | Scientific Programme, Communities Handbook, PeoplePulse protocol, Demystifying ELIXIR slides; 98 ELITMa pages and 6 documents. | Named documents saved. Some ELITMa modules are unfinished; videos remain links. |
| F1000 ELIXIR Gateway | 60 articles, 69 documents, 460 posters, 144 slide records, with PDFs. | Unique counts match all four listing totals; every discovered publication PDF is present. |
| Zenodo ELIXIR community | 199 records and 220 document files. | Counts match; previously missed ODS and HTML files saved. Media and archives excluded. |
| Systems Biology publications | Named event report, opinion article and arXiv paper, with PDFs. | All three saved. |
| bio.tools | 34,819 unique records; no duplicates in the new ordered collection. | Matches final total, but totals grew from 34,804 during collection. Flagged as changing rather than a verified snapshot. |
| TeSS | 10,323 events, including past events, and 3,677 materials. | Counts match; external training websites are outside scope. |
| FAIRsharing and internal sources | Explicitly deferred in the source registry. | Need account access, permissions or files; project plans also need budget redaction. |

## Extension — 10 November 2026

All 16 enabled extension sources finished, with no pending or failed downloads. Added **1,238 files, 1.68 GB**, including reused documents and versions; the public collection contains **6,889 files, 5.06 GB**. Paths, sizes and content hashes passed validation.

| Added coverage | Result |
| --- | --- |
| CORDIS | STEERS, CONVERGE and EXCELERATE: fact sheets, results, reporting and linked public documents. |
| Project Zenodo outputs | 52 / 85 / 95 versioned records; all three catalogue totals match with no duplicate IDs. Bulk research-data attachments and media remain excluded. |
| Eight additional Nodes | 212 saved URLs across the configured team, project and roadmap pages. Swiss group results and the named participant lookup are rendered; these are bounded selections, not complete site crawls. |
| Systems Biology literature | 1,201 Europe PMC review records; catalogue total matches, metadata and abstracts only. |
| Example projects | Canonical 24-compute and FAIR-FEGA pages retained. A proposed alternate FAIR-FEGA URL was confirmed 404 in both Chrome and Browser and excluded. |

Participation, group-activity and bid-outcome inputs remain deferred for permission and files. Existing FAIRsharing and internal-source gaps above remain unchanged.

## Public Zenodo plans — 10 November 2026

`zenodo-project-plans` collected **43 matching records and 35 document attachments**, with no pending or failed downloads. The source folder contains **80 files, 53.9 MB**, including two search pages and 28 reused downloads. All document checksums match Zenodo; offline resume passes. Eight image attachments and three XML copies remain excluded.

All five Platform work plans and both BFSP versions were already in the published snapshot. This search also found the [ELIXIR–Euro-BioImaging action plan](https://zenodo.org/records/14743742), which has no ELIXIR community tag, plus related proposals and roadmaps. The 43 matches are not 43 project plans. Coverage is complete for the configured query; unidentified or restricted plans can remain missing. These additions are local and await the next S3 snapshot.

## S3 snapshot

Snapshot **`20261110T134028Z`** contains **6,891 files, 5.07 GB**, including both original Perun CSV exports in `input/perun/`. Their remote SHA-256 checksums were verified. The Perun data is restricted and stays out of Git; browser cookies and session files are excluded from both Git and the snapshot.

## Run or extend

```bash
uv run python src/scraping/run.py
uv run python src/scraping/run.py all --cookies .scraping/cookies.json
uv run python src/scraping/run.py f1000 zenodo
uv run python src/scraping/run.py biotools --refresh
uv run python src/scraping/run.py cordis-steers zenodo-steers project-pages
uv run python src/scraping/run.py zenodo-project-plans
```

Omit names to list sources. [sources.py](../src/scraping/sources.py) covers every numbered entry in [data sources](data-sources.md), including deferred inputs. Add websites there; add unusual discovery functions in [discovery.py](../src/scraping/discovery.py). The runner stays shared.

Rerunning reuses saved responses, rediscovers their links and retries unfinished downloads. Public files already collected by another source are copied into the new source folder with their original retrieval date. Files are saved atomically; `--refresh` fetches selected sources again. New filenames include a content hash, so changed responses preserve the previous files. The [URL index](../data-sources-scraping.jsonl) records source, parent URL, path, retrieval time, access level and outcome. Retrieval time is not the document's publication date. Use the latest row per source/URL for current state and older rows for comparisons; `discovery_status` is separate from download `status`. A null URL marks a source summary or an input awaiting a URL.

The browser restores cookies and pauses for manual verification. `--verification-timeout 60` lets other hosts continue after an unresolved check; the default waits. Import public files downloaded through Browser, then rerun their source:

```bash
uv run python src/scraping/run.py elixir --import-file /path/to/file.pdf --url 'https://original-download-url'
```

Each contributor exports their own browser cookies into `.scraping/`. This git-ignored folder at the repository root holds the private browser profile and session, outside `data/` and S3 uploads. Keep it to reuse verification; never import it as data.

Extensions cover three EU projects, their versioned Zenodo outputs, eight additional Node sites and a bounded Systems Biology literature query. Each has its own source folder under `data/input/`. Add projects through `EU_PROJECTS`; keep independent catalogue queries in separate sources so count checks remain meaningful. Restricted participation, activity and bid records are deferred. The access label is descriptive; restricted inputs need permission controls in storage and extraction before collection is enabled.

Scope: latest news listings, no jobs or old website archives, full bio.tools/TeSS catalogues, video links only. Explicit project announcements in the registry are exceptions. Discarded downloads were deleted; their exclusions remain in the index. No LLM extraction.
