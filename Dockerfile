FROM node:24-bookworm-slim AS dashboard
WORKDIR /build
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY dashboard/ ./
RUN npm run build

FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv
WORKDIR /app
COPY server/pyproject.toml server/uv.lock ./
RUN uv sync --frozen --no-dev
COPY server/atlas_api ./atlas_api
COPY server/tests ./tests
COPY --from=dashboard /build/dist ./static
COPY release/ ./release/
ENV PATH="/app/.venv/bin:$PATH"
ENV ATLAS_STATIC_DIR=/app/static ATLAS_RELEASE_DIR=/app/release
CMD ["sh", "-c", "exec uvicorn atlas_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
