import { createReadStream, existsSync, statSync } from "node:fs";
import type { IncomingMessage, ServerResponse } from "node:http";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const database = fileURLToPath(new URL("../graph/build/graph.sqlite", import.meta.url));

function serveDatabase(_request: IncomingMessage, response: ServerResponse) {
  if (!existsSync(database)) {
    response.statusCode = 404;
    response.end("The atlas database is missing. Build it with: uv run --project graph biotope graph build --format sqlite");
    return;
  }
  response.setHeader("Content-Type", "application/vnd.sqlite3");
  response.setHeader("Content-Length", statSync(database).size);
  response.setHeader("Cache-Control", "no-cache");
  createReadStream(database).pipe(response);
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: "atlas-database",
      configureServer(server) {
        server.middlewares.use("/graph.sqlite", serveDatabase);
      },
      configurePreviewServer(server) {
        server.middlewares.use("/graph.sqlite", serveDatabase);
      },
    },
  ],
  server: { host: "localhost", port: 5180 },
  preview: { host: "localhost", port: 5180 },
});
