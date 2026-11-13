# Atlas serving

The deployment uses two Railway services: PostgreSQL 18 with a persistent volume, and a FastAPI service that also serves the built React dashboard. PostgreSQL is reachable through Railway's private network. The dashboard and read-only API are public.

Public update-request submission is available when `ATLAS_REQUEST_DATABASE_URL` is configured with a separate insert-only login in the same database. Run the existing permissions command to provision it. Requests remain pending in `atlas_feedback.update_request`, which survives graph release imports. See [update requests](../docs/update-requests.md) for setup, the API, and the future tier-0 review flow.

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

## Quick local SQLite dashboard

From the repository root:

```bash
python3 scripts/dashboard.py
```

This opens `graph/build/graph.sqlite` through a local API and starts the same dashboard at http://127.0.0.1:5180. To use another file, pass its path as the first argument. Only the SQLite file is required; matching `schema_config.yaml` and `provenance.json` beside it add descriptions and source evidence. No PostgreSQL or release import is needed. The source file is opened read-only, copied into memory and indexed there. Restart the command after rebuilding; Ctrl+C stops both processes.

Local keyword search uses SQLite FTS5 with words and quoted phrases combined with AND. It supports the same type filters and pagination, but has different ranking and does not implement PostgreSQL's fuzzy matching, `OR` or exclusions. See [dashboard modes](../dashboard/README.md).

For a standalone SQLite API, set `ATLAS_SQLITE_PATH` to an absolute snapshot path and run the same Uvicorn command below. SQLite mode is explicit; without that variable, the API requires `DATABASE_URL`. Railway uses PostgreSQL and must leave `ATLAS_SQLITE_PATH` unset.

## Local PostgreSQL API

Use separate owner and reader credentials. For a disposable local PostgreSQL 18 instance, run from the repository root:

```bash
docker run -d --name atlas-sql-postgres \
  -e POSTGRES_PASSWORD=atlas-local-admin -e POSTGRES_DB=atlas \
  -p 127.0.0.1:55432:5432 postgres:18
export DATABASE_ADMIN_URL='postgresql://postgres:atlas-local-admin@127.0.0.1:55432/atlas'
export DATABASE_URL='postgresql://atlas_reader:atlas-local-reader@127.0.0.1:55432/atlas'
uv sync --project server
uv run --directory server python -m atlas_api.permissions
uv run --directory server python -m atlas_api.import_release ../data/releases/20261111
ATLAS_TRACE_DIR=/tmp/atlas-sql-api-traces uv run --directory server \
  uvicorn atlas_api.main:app --host 127.0.0.1 --port 8811
```

These passwords are for the disposable local database only. Provisioning removes database CREATE/TEMP and public-schema CREATE privileges inherited through PUBLIC; use a dedicated database. It configures the reader and grants access to an existing release. Imports apply reader grants to the replacement schema within the import transaction. The API refuses owner, privileged, role-switching or write-capable connections, including column-level write grants and callable custom SECURITY DEFINER functions. Import commands require `DATABASE_ADMIN_URL`; the API uses only `DATABASE_URL`.

A dashboard build in `dashboard/dist` is served directly by FastAPI, or set `ATLAS_STATIC_DIR` explicitly. The SQLite dashboard command above remains available.

## API and search

`/docs` and `/openapi.json` describe the endpoints. `/api/release` exposes the release identity, manifest, table counts and import time; `/api/schema` exposes the topology metadata. `/healthz` checks the database and loaded release.

`/api/search?q=genomics&type=Tool&limit=30&offset=0` returns ranked records and type counts. `type` is optional. Titles, names and aliases carry the highest weight; descriptions and evidence supply the body. PostgreSQL GIN full-text indexes support the document search, and trigram indexes support name substrings and similar names. Quoted phrases, `OR` and exclusions use PostgreSQL's web-search syntax and disable the fuzzy-name fallback. The maximum page size is 100.

`/api/record?type=Tool&id=...` returns fields, their definitions and resolved source evidence. `/api/relations` returns paginated incoming/outgoing relationships with links to the relationship records. The existing dashboard uses `/api/home`, `/api/person`, `/api/initiative`, `/api/node`, `/api/kind`, `/api/reviews` and `/api/overlap`.

SQL is available on Railway and in local PostgreSQL mode. `/api/release` reports SQL availability and the running API code fingerprint. `GET /api/schema?format=sql` adds PostgreSQL names, types, keys and query limits to the release's Biotope descriptions. The default schema response remains topology metadata.

The local CQ iteration adds `detail=summary` for a compact table catalogue with relationship directions, and `tables=initiative,holdsrole` to select full definitions. Descriptions still come from the served build. Search accepts case-insensitive type names and returns 422 with valid types for an unknown type, so a filter mistake cannot silently look like missing evidence. SQL syntax errors also include quoting guidance. These follow-up changes have not been deployed to Railway.

`POST /api/query` accepts `{"sql":"SELECT kind, count(*) FROM initiative GROUP BY kind","limit":1000}`. It returns positional rows, column metadata, release/request identities and truncation information. The [skill API reference](../skills/agentic-elixir/references/api.md) covers requests, errors and pagination.

The reader role and read-only transaction enforce database permissions. The SQL parser accepts one read query over documented tables and supported built-ins, rejecting writes, commands, row locks and custom routines/types/operators. FROM functions require `WITH ORDINALITY` to prevent scalar field notation from invoking unsupported functions.

SQL requests have a five-second deadline, 500 ms lock timeout, two concurrent slots, and response caps of 1,000 rows and 1 MB. Rows are fetched in small batches; aggregates still use the complete input. These limits do not bound all PostgreSQL intermediate memory use. GET requests retain their ten-second timeout. Timeouts return errors, never successful partial results.

Set `ATLAS_TRACE_DIR` to save API request methods, URLs, bodies, status, timing, sizes, request IDs and complete responses. Headers and credentials are excluded. Keep these files with the eval experiment; they contain user queries and evidence.

## Railway deployment and refresh

The app's `DATABASE_URL` uses the `atlas_reader` login over PostgreSQL's private network. `DATABASE_ADMIN_URL` references `${{Postgres.DATABASE_URL}}` for provisioning and imports. Railway runs `sh -c 'python -m atlas_api.permissions && python -m atlas_api.bootstrap'` before deployment with a 300-second timeout. Provisioning configures reader permissions; bootstrap imports only when the release manifest changes.

The app uses one replica in the same region as PostgreSQL, checks `/healthz` with a 120-second timeout, and restarts on failure up to three times. The Dockerfile supplies the start command. For an importer/index change against the same release, explicitly rerun `atlas_api.import_release` through Railway SSH.

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

The SQL deployment was verified publicly on 2026-11-11: aggregates, joins/CTEs, generated schema, structured SQL errors, error recovery, truncation, write/lock/system-table rejection, search and dashboard assets passed. The release manifest, record counts and import time were unchanged. Responses and verification results are saved under `eval/results/railway-sql-deploy-20261111/`.

```bash
npm run build --prefix dashboard
uv run --directory server python -m unittest discover -s tests -v
```

Without `DATABASE_URL`, the schema/checksum and SQLite fixture tests run. Set `ATLAS_TEST_SQLITE` to an absolute path to a built snapshot to also check every dashboard view and record type against it. These tests cover both bare snapshots and optional metadata, indexed search, pagination, read-only access and an unchanged source file.

With PostgreSQL, import tests use `DATABASE_ADMIN_URL` and a temporary schema to check typed round-trips, repeat imports and rollback after failure. Set `DATABASE_URL` to the reader and `ATLAS_RELEASE_DIR` to the imported release to compare every field of every record and check all dashboard queries, search pagination, filtering, phrase behavior, provenance, relationships and index availability. Set `ATLAS_TEST_BASE_URL` to test live HTTP validation, missing records and read-only routes.

With a Railway SSH key registered, run the full suite through the deployed service's private connection. Alternatively, use a one-off service with the same image and private database connection, the test command as its start command, and restart policy `NEVER`; remove it when checks finish. Do not add the test suite to the app's normal pre-deploy command.

```bash
npx --yes @railway/cli ssh \
  --project 6b9e8f0f-9a31-4bd7-9985-6cb90c74c635 \
  --service e98db560-fc07-465e-96cd-9d62bc520dfd \
  --environment 060c6891-ef4f-4b0b-9bac-8cf6a234a4e3 \
  -- env ATLAS_TEST_BASE_URL=http://127.0.0.1:8000 python -m unittest discover -s tests -v
```

For the local SQL tests, set `ATLAS_TEST_ADMIN_URL` to the disposable owner's URL. These tests create and delete their own temporary database and reader role. They verify direct write denial, startup checks, parser boundaries, repeated/failed imports, error recovery, limits and trace completeness:

```bash
ATLAS_TEST_ADMIN_URL="$DATABASE_ADMIN_URL" uv run --directory server \
  python -m unittest discover -s tests -p test_query.py -v
```
