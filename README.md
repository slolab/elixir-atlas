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

- `data/input/<source>/`: raw data, collected by hand. Can have strctured (tabled) and unstrctured (text files, presentations)
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

`pull` never overwrites your local changes. `push` refuses if S3 has a snapshot you haven't pulled.
