# Atlas serving

The deployment uses two Railway services: PostgreSQL 18 with a persistent volume, and a FastAPI service that also serves the built React dashboard. PostgreSQL is reachable through Railway's private network. The dashboard and read-only API are public.

- Dashboard: https://atlas-production-d392fb6d.up.railway.app
- API documentation: https://atlas-production-d392fb6d.up.railway.app/docs
- Railway project: https://railway.com/project/6b9e8f0f-9a31-4bd7-9985-6cb90c74c635

## Schema and releases

`atlas_api/schema.py` generates SQL from the immutable release's `schema_config.yaml`, which Biotope generates from topology. Each node and edge becomes a table. Property types become text, text arrays, bigint, double precision or boolean; optional properties allow nulls. Every table has a primary key, edges have endpoint foreign keys and indexes, and provenance references are checked.

The release schema is used instead of the current Python topology so an older release cannot accidentally acquire a newer shape. Unsupported types, table/column mismatches, invalid references, null violations and checksum failures stop the import. No separately maintained ORM schema is needed.

The importer verifies all four manifest checksums, validates SQLite integrity, loads the complete release, compares table counts and builds search indexes. An advisory lock serializes imports. Loading and replacing the `atlas` schema happen in one transaction: a failure preserves the previously served release. Refreshes replace a generated snapshot; they do not merge application edits.

Generate a reviewable SQL schema from a release:

```bash
uv run --directory server python -m atlas_api.import_release ../data/releases/20261111 --schema-only
```

## Local API

Set `DATABASE_URL` to a PostgreSQL database you control, then run from the repository root:

```bash
uv sync --project server
uv run --directory server python -m atlas_api.import_release ../data/releases/20261111
uv run --directory server uvicorn atlas_api.main:app --host 127.0.0.1 --port 8000
```

Start the dashboard separately with `npm run dev --prefix dashboard`. A production dashboard build in `dashboard/dist` is served directly by FastAPI, or set `ATLAS_STATIC_DIR` explicitly.

## API and search

`/docs` and `/openapi.json` describe the endpoints. `/api/release` exposes the release identity, manifest, table counts and import time; `/api/schema` exposes the topology metadata. `/healthz` checks the database and loaded release.

`/api/search?q=genomics&type=Tool&limit=30&offset=0` returns ranked records and type counts. `type` is optional. Titles, names and aliases carry the highest weight; descriptions and evidence supply the body. PostgreSQL GIN full-text indexes support the document search, and trigram indexes support name substrings and similar names. Quoted phrases, `OR` and exclusions use PostgreSQL's web-search syntax and disable the fuzzy-name fallback. The maximum page size is 100.

`/api/record?type=Tool&id=...` returns fields, their definitions and resolved source evidence. `/api/relations` returns paginated incoming/outgoing relationships with links to the relationship records. The existing dashboard uses `/api/home`, `/api/person`, `/api/initiative`, `/api/node`, `/api/kind`, `/api/reviews` and `/api/overlap`.

Queries are parameterized, API transactions are read-only, and statements have a ten-second timeout. There is no arbitrary SQL endpoint, download of the source database or public write/import endpoint. Source API updates and the agentic plugin are deferred; they can reuse the record, relationship and search endpoints.

## Railway deployment and refresh

The app's `DATABASE_URL` references `${{Postgres.DATABASE_URL}}`. The app uses one replica in the same region as PostgreSQL. Railway's service settings run `python -m atlas_api.bootstrap` as the pre-deploy command with a 300-second timeout, check `/healthz` with a 120-second timeout, and restart on failure up to three times. The Dockerfile supplies the start command. Bootstrap imports only when the release manifest changes. For an importer/index change against the same release, explicitly rerun `atlas_api.import_release` through Railway SSH.

Prepare an upload containing only the server, dashboard, deployment files and the selected validated release:

```bash
python3 scripts/prepare_deploy.py data/releases/20261111
```

The command prints a temporary directory. Deploy that directory:

```bash
npx --yes @railway/cli up PREPARED_DIRECTORY --path-as-root \
  --project 6b9e8f0f-9a31-4bd7-9985-6cb90c74c635 \
  --service e98db560-fc07-465e-96cd-9d62bc520dfd \
  --environment 060c6891-ef4f-4b0b-9bac-8cf6a234a4e3 --detach
```

To publish a new data release, prepare and deploy its directory the same way. The current deployment uses a local source upload; pushing Git alone does not deploy it.

## Validation

Release `20261111` was verified on 2026-11-11: all 10 checks passed against Railway PostgreSQL, including equality of every field in all 72,574 records across 38 graph tables. The checks ran in a temporary validation service, which was removed afterward. Browser checks covered the home view, ranked search, type filtering, project details, evidence, relationships and overlap.

```bash
npm run build --prefix dashboard
uv run --directory server python -m unittest discover -s tests -v
```

Without `DATABASE_URL`, only schema/checksum tests run. With PostgreSQL, import tests use a temporary schema and check typed round-trips, repeat imports and rollback after failure. Set `ATLAS_RELEASE_DIR` to the imported release to compare every field of every record and check all dashboard queries, search pagination, filtering, phrase behavior, provenance, relationships and index availability. Set `ATLAS_TEST_BASE_URL` to test live HTTP validation, missing records and read-only routes.

With a Railway SSH key registered, run the full suite through the deployed service's private connection. Alternatively, use a one-off service with the same image and private database connection, the test command as its start command, and restart policy `NEVER`; remove it when checks finish. Do not add the test suite to the app's normal pre-deploy command.

```bash
npx --yes @railway/cli ssh \
  --project 6b9e8f0f-9a31-4bd7-9985-6cb90c74c635 \
  --service e98db560-fc07-465e-96cd-9d62bc520dfd \
  --environment 060c6891-ef4f-4b0b-9bac-8cf6a234a4e3 \
  -- env ATLAS_TEST_BASE_URL=http://127.0.0.1:8000 python -m unittest discover -s tests -v
```
