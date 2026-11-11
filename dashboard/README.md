# ELIXIR Atlas dashboard

A local, read-only explorer for the atlas database. It opens `../graph/build/graph.sqlite` in the browser with sql.js, so the data stays on this machine.

```bash
npm install
npm run dev
```

Then open http://localhost:5180. Build the database first with `uv run --project graph biotope graph build --format sqlite` from the repository root. The database holds Perun personal data: keep the server on localhost and do not publish a build of this app together with the database.
