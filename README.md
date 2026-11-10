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
