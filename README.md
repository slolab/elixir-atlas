# Elixir Atlas

[shared document](https://docs.google.com/document/d/13I082LFa2bPSmwlXlhX_Peryn-iyYLIKuryNqrMYnJ4/edit?tab=t.0#heading=h.whxawsumg2qw)

## Setup

```bash
uv sync
cp .env.template .env  # then fill it in
uv run scripts/data.py pull
```

## Data

`data/` is not in git. S3 keeps timestamped snapshots and releases that never change.

- `data/input/<source>/`: original scraped or manually collected data: API responses, web pages and documents.
- `data/extracted/<source>/`: structured data extracted from unstrctured `input/`.
- `data/releases/<id>/`: the built data product.

A snapshot holds `input/` and `extracted/` together.

```bash
uv run scripts/data.py list
uv run scripts/data.py pull [id]          # newest snapshot by default
uv run scripts/data.py push               # input/ + extracted/ as a new snapshot
uv run scripts/data.py pull-release [id]  # newest release by default
uv run scripts/data.py push-release <id>
```

`pull` never overwrites your local changes. `push` refuses if S3 has a snapshot you haven't pulled. Behaviour:

- First pull, no .snapshot.json. Every file already on disk counts as yours and is kept. Files you do not have are downloaded.
- You edited or added files after a pull. Those stay. Untouched files update to S3.
- You deleted a file that was in the base. It stays deleted, even if S3 still has it.

Scraping: [sources, coverage and usage](docs/data-sources-scraping.md).

Evaluation: [CQ sets, runs and Argilla](eval/README.md).

Dashboard: `python3 scripts/dashboard.py` opens the local `graph/build/graph.sqlite` snapshot. See [local SQLite and API modes](dashboard/README.md).

Serving: [PostgreSQL, API, search and Railway deployment](server/README.md).

## Agentic ELIXIR skill

Two versions are available:

- `dist/agentic-elixir.zip`: the complete dated release, for cloud and local sessions without network access.
- `dist/agentic-elixir-api.zip`: the live API version, for agents with direct HTTP access to the Atlas host. Install as `agentic-elixir-api`; it requires no credentials and follows the release currently served on Railway.

[Agentic ELIXIR](skills/agentic-elixir/SKILL.md) answers the [user stories](eval/user_stories.md) from a complete Atlas release bundled in the skill. It searches records and runs read-only SQLite queries with Python's standard library. It works in cloud and local sessions without network access, connectors, credentials or package installation. Installing a new release ZIP updates its data; Railway updates do not change an already installed skill.

Build the release package from this checkout:

```bash
uv run --project server python scripts/build_skill.py data/releases/20261112
```

Upload `dist/agentic-elixir.zip` through Claude's skill installation screen. For a filesystem-based agent, install the generated complete folder:

```bash
npx skills add ./dist/agentic-elixir -g
```

The installer lets you choose agents. To select one explicitly, add `-a codex`, `-a claude-code`, `-a opencode` or `-a hermes-agent`. The installer requires Node.js; the installed skill needs only Python 3 with SQLite. The source folder alone has no data: install the built package, not `skills/agentic-elixir` directly.

Check the generated package:

```bash
python3 dist/agentic-elixir/scripts/atlas.py verify
python3 dist/agentic-elixir/scripts/atlas.py search metabolomics --type Initiative
```

The build verifies the immutable release checksums and includes all graph records, schema descriptions and provenance. A separate full-text index supplies search; its excerpts are previews, while records and SQL return the original fields. The live API remains available for the dashboard and other clients.

Build the API-only ZIP with `python3 -m zipfile -c dist/agentic-elixir-api.zip skills/agentic-elixir-api`, or install its source folder directly with `npx skills add ./skills/agentic-elixir-api -g`. The two skill names are distinct so both can be installed together.
