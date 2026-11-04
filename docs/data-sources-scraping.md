# Scraping

## Coverage — 4 November 2026

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

## Run or extend

```bash
uv run python src/scraping/run.py
uv run python src/scraping/run.py all --cookies .scraping/cookies.json
uv run python src/scraping/run.py f1000 zenodo
uv run python src/scraping/run.py biotools --refresh
```

Omit names to list sources. [sources.py](../src/scraping/sources.py) covers every numbered entry in [data sources](data-sources.md), including deferred inputs. Add websites there; add unusual discovery functions in [discovery.py](../src/scraping/discovery.py). The runner stays shared.

Rerunning reuses saved responses, rediscovers their links and retries unfinished downloads. Files are saved atomically; `--refresh` fetches selected sources again. The [URL index](../data-sources-scraping.jsonl) records source, parent URL, saved path and outcome. Repeated history was compacted; future runs append updates. Use the latest row per source/URL; `discovery_status` is separate from download `status`. A null URL marks a source summary or an input awaiting a URL.

The browser restores cookies and pauses for manual verification. `--verification-timeout 60` lets other hosts continue after an unresolved check; the default waits. Import public files downloaded through Browser, then rerun their source:

```bash
uv run python src/scraping/run.py elixir --import-file /path/to/file.pdf --url 'https://original-download-url'
```

Each contributor exports their own browser cookies into `.scraping/`. This git-ignored folder at the repository root holds the private browser profile and session, outside `data/` and S3 uploads. Keep it to reuse verification; never import it as data.

Scope: latest news listings, no jobs or old website archives, full bio.tools/TeSS catalogues, video links only. Discarded downloads were deleted; their exclusions remain in the index. No LLM extraction.
