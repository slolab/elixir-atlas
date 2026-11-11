import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: { host: "localhost", port: 5180, proxy: { "/api": "http://127.0.0.1:8000", "/healthz": "http://127.0.0.1:8000" } },
  preview: { host: "localhost", port: 5180 },
});
