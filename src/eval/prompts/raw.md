The raw data are mounted read-only under `/workspace/data/input`, one folder per source: web pages, PDFs, API responses and other documents. `/workspace/data-sources-scraping.jsonl` gives each file's `path`, relative to `/workspace`, and the `url` it was retrieved from. Cite these URLs, not local paths. These files are your only evidence.

`pdftotext`, `rg` and `jq` are installed. `uv run --with <package> python …` gives you any Python package.

Web search and web fetch are not available. Do not use the web.
