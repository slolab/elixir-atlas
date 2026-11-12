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

## Find by topic

The **Find by topic** page supports the researcher workflow in use case C1. Choose research areas to find matching Communities, contacts and joining links, followed by Community resources, papers, topic-tagged tools and training. Selecting several areas includes matches to any of them. Communities matching more selected areas appear first, followed by those linked through tools.

For a local preview, use the v3 release or a newer build:

```bash
python3 scripts/dashboard.py data/releases/20261112/graph.sqlite --port 5181
```

Open http://127.0.0.1:5181/#/topic. Start with **Systems biology** for the metabolic modelling example. Resource labels distinguish recommendations and development from catalogue listings. Expand a label or a Community's match explanation to inspect evidence; record links open the full fields and sources.

Community resources and papers cover their wider work and are not necessarily specific to the selected topic. Training and events come from the collected snapshot, so missing results do not establish that nothing exists. The page exposes result limits when applicable: 60 additional tools, 30 paper/Community matches, 40 training materials and 40 upcoming events.
