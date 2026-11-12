# ELIXIR Atlas dashboard

A read-only explorer with two supported modes: a quick local SQLite snapshot, and the public Railway deployment backed by PostgreSQL. Both use the same React dashboard and named API endpoints.

## Quick local SQLite

From the repository root, with Python 3, uv and Node.js installed:

```bash
python3 scripts/dashboard.py
```

Open http://127.0.0.1:5180. The launcher defaults to `graph/build/graph.sqlite`, installs missing dashboard dependencies, and starts the local API and Vite together. No PostgreSQL, `DATABASE_URL`, release manifest or import is needed. Ctrl+C stops both processes. Restart after rebuilding the snapshot.

Choose another build or release:

```bash
python3 scripts/dashboard.py data/releases/20261111/graph.sqlite
```

`npm run dev --prefix dashboard` starts the same local mode. Inside `dashboard`, use `npm run dev`. Pass `--port 5181` to the Python launcher if needed.

The snapshot stays unchanged. The API copies it into memory, builds relationship and SQLite FTS5 search indexes, and serves read-only queries. Search supports words and quoted phrases, type filters and pagination. Words are combined with AND; PostgreSQL's fuzzy matching, `OR` and exclusions are not provided in local mode, and ranking can differ.

Bare SQLite supports all existing views, record fields and relationships. Put the matching `schema_config.yaml` and `provenance.json` beside it to include field descriptions, exact property types and detailed source evidence. Missing evidence is shown explicitly.

## PostgreSQL and Railway

See [server setup, import and deployment](../server/README.md). The production browser requests data from PostgreSQL through the API; it does not download the SQLite release.

For local frontend development against a separately running API on localhost:8000:

```bash
npm ci --prefix dashboard
npm run dev:api --prefix dashboard
```

Set `ATLAS_API_URL` to change the Vite proxy target. `npm run build --prefix dashboard` builds the production frontend for FastAPI; it does not start or bundle the local SQLite launcher.

The existing project, person, Node, overlap and review views use the API. Keyword search covers all record types with ranked results, type filters and pagination. Every result has a record-and-evidence view, and node records also show their relationships.

The project owner confirmed public access to the complete 20261111 release on 2026-11-11. There is no login or editing interface.

## Atlas tab

`#/atlas` lists the competency questions of `eval/cqs/atlas_261111` by use case. Choosing one shows the cards it needs (Community, Topic, Node, Project, Person, Plan item, Output, Tool, training…), each with all its items. Picking an item narrows every other card to what the question's routes (relationship tables) connect to it; picks on several cards intersect. Below the cards, each connection is listed with its properties (role, task, funding…), quote and source. An empty narrowed card means no public record is linked, not that none exists.

Questions, their cards and routes are in `server/atlas_api/atlas_questions.yaml`; cards are defined over entity tables in `server/atlas_api/atlas.py` (a Community is an Initiative of kind `community`). Endpoints: `GET /api/atlas` (questions, cards with counts, routes), `GET /api/atlas/items?card=&q=`, `GET /api/atlas/pick?question=&picks=card=id,card=id`.
