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

[Agentic ELIXIR](skills/agentic-elixir/SKILL.md) answers the [user stories](eval/user_stories.md) through the public Atlas API, using enriched keyword searches, relationships and source evidence. The package contains only the skill and its API reference; no credentials, local data or runtime dependencies are needed beyond an agent that can make HTTP requests.

Install from this checkout:

```bash
npx skills add ./skills/agentic-elixir -g
```

After the skill is published to this repository, install remotely:

```bash
npx skills add slolab/elixir-atlas --skill agentic-elixir -g
```

The installer lets you choose agents. To select one explicitly, add `-a codex`, `-a claude-code`, `-a opencode` or `-a hermes-agent`. See the installer's [supported agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md). The installer requires Node.js; the installed skill does not.

To create a ZIP from the repository root:

```bash
mkdir -p dist
python3 -m zipfile -c dist/agentic-elixir.zip skills/agentic-elixir
```

Extract the ZIP and install its `agentic-elixir` folder with `npx skills add ./agentic-elixir -g`, or place that folder in your agent's skills directory.
