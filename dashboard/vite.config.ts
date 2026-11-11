import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const api = process.env.ATLAS_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: { host: "localhost", port: 5180, proxy: { "/api": api, "/healthz": api } },
  preview: { host: "localhost", port: 5180 },
});
