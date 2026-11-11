# ELIXIR Atlas dashboard

A public, read-only explorer served by the Atlas API. The browser requests records from PostgreSQL through named API endpoints. It does not download the SQLite release.

```bash
npm ci
npm run dev
```

Start the API on localhost:8000 first, then open http://localhost:5180. Vite forwards `/api` and `/healthz` to the API. See [server setup and deployment](../server/README.md).

The existing project, person, Node, overlap and review views use the API. Keyword search covers all record types with ranked results, type filters and pagination. Every result has a record-and-evidence view, and node records also show their relationships.

The project owner confirmed public access to the complete 20261111 release on 2026-11-11. There is no login or editing interface.
