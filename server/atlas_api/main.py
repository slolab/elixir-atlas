import os
import re
import hashlib
import threading
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg import errors, sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout
from psycopg import Error as DatabaseError
from pydantic import BaseModel, Field

from . import views
from .sqlite_snapshot import Snapshot
from . import query
from .permissions import check_reader
from .schema import sql_schema
from .tracing import trace


API_REVISION = hashlib.sha256(b"".join(path.name.encode() + path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py")))).hexdigest()
QUERY_SLOTS = threading.BoundedSemaphore(2)


@asynccontextmanager
async def lifespan(app):
    app.state.snapshot = None
    app.state.trace_directory = os.environ.get("ATLAS_TRACE_DIR")
    if path := os.environ.get("ATLAS_SQLITE_PATH"):
        with closing(Snapshot(path)) as snapshot:
            app.state.snapshot = snapshot
            yield
        return
    with ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=8, timeout=10, kwargs={"row_factory": dict_row, "prepare_threshold": None}) as pool:
        with pool.connection() as conn:
            check_reader(conn)
        app.state.pool = pool
        yield


app = FastAPI(title="ELIXIR Atlas API", version="1.0.0", description="Read-only access to the Atlas release, records, relationships, source evidence and keyword search.", lifespan=lifespan)
app.middleware("http")(trace)


@app.exception_handler(RequestValidationError)
def invalid_request(request, error):
    return JSONResponse(status_code=422, content={"request_id": request.state.request_id, "detail": [
        {key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()
    ]})


def connection(request: Request):
    if snapshot := request.app.state.snapshot:
        with snapshot.lock:
            yield snapshot
        return
    with request.app.state.pool.connection() as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            conn.execute("SET LOCAL search_path TO atlas, public")
            conn.execute("SET LOCAL statement_timeout TO '10s'")
            yield conn


Database = Annotated[object, Depends(connection)]
RecordId = Annotated[str, Query(min_length=1, max_length=500)]


@app.exception_handler(PoolTimeout)
@app.exception_handler(errors.QueryCanceled)
def unavailable(request, error):
    return JSONResponse(status_code=503, content={"detail": "The atlas is busy. Please try again shortly."})


@app.get("/healthz")
def health(db: Database):
    if isinstance(db, Snapshot):
        return {"status": "ok", "release": db.release["id"], "mode": "sqlite"}
    release = views.one(db, "SELECT id FROM release")
    if release is None:
        raise HTTPException(503, "No release loaded")
    return {"status": "ok", "release": release["id"]}


@app.get("/api/release")
def release(db: Database):
    if isinstance(db, Snapshot):
        return {**db.release, "api": {"revision": API_REVISION, "sql": False}}
    return {**views.one(db, "SELECT id, manifest, counts, imported_at FROM release"), "api": {"revision": API_REVISION, "sql": True}}


@app.get("/api/schema")
def topology(db: Database, format: Literal["topology", "sql"] = "topology", tables: str | None = Query(default=None, max_length=2000), detail: Literal["full", "summary"] = "full"):
    if format == "sql":
        if isinstance(db, Snapshot):
            raise HTTPException(501, "SQL querying requires PostgreSQL mode")
        current = views.one(db, "SELECT id, manifest, topology FROM release")
        definitions = sql_schema(current["topology"])
        if isinstance(tables, str):
            selected = {name.strip().removeprefix("atlas.") for name in tables.split(",")}
            unknown = selected - {name.removeprefix("atlas.") for name in definitions}
            if unknown:
                raise HTTPException(422, f"Unknown tables: {', '.join(sorted(unknown))}. Use /api/schema?format=sql&detail=summary to discover tables.")
            definitions = {name: value for name, value in definitions.items() if name.removeprefix("atlas.") in selected}
        if detail == "summary":
            definitions = {name: {key: value for key, value in entity.items() if key != "columns"} | {
                "references": {column: value["references"] for column, value in entity["columns"].items() if "references" in value and column != "biotope_provenance_id"}
            } for name, entity in definitions.items()}
        return {"dialect": "PostgreSQL", "release": current["id"], "api_revision": API_REVISION,
                "schema_sha256": current["manifest"]["files"]["schema_config.yaml"]["sha256"],
                "tables": definitions, "functions": sorted(query.FUNCTIONS), "cast_types": sorted(query.TYPES),
                "requirements": ["Quote column identifiers with double quotes, especially reserved words such as \"end\".", "FROM functions require WITH ORDINALITY, e.g. unnest(pages) WITH ORDINALITY AS u(url, position)."],
                "limits": {"rows": query.MAX_ROWS, "bytes": query.MAX_BYTES, "timeout_ms": query.TIMEOUT_MS, "concurrency": 2}}
    if isinstance(db, Snapshot):
        return db.schema
    return views.one(db, "SELECT topology FROM release")["topology"]


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=32_000)
    limit: int = Field(default=query.MAX_ROWS, ge=1, le=query.MAX_ROWS)


@app.post("/api/query")
def query_database(body: QueryRequest, request: Request, db: Database):
    if isinstance(db, Snapshot):
        raise HTTPException(501, "SQL querying requires PostgreSQL mode")
    request_id = request.state.request_id
    if not QUERY_SLOTS.acquire(blocking=False):
        return JSONResponse(status_code=503, content={"request_id": request_id, "error": {"code": "busy", "message": "Two queries are already running. Retry shortly."}})
    try:
        current = views.one(db, "SELECT id, manifest, topology FROM release")
        result = query.execute(db, body.sql, body.limit, current, API_REVISION)
        return JSONResponse(content={**result, "request_id": request_id})
    except query.QueryError as error:
        return JSONResponse(status_code=error.status, content={"request_id": request_id, "error": {"code": error.code, "message": str(error), "position": error.position, "hint": error.hint}})
    except DatabaseError as error:
        timeout = isinstance(error, (errors.QueryCanceled, errors.LockNotAvailable))
        return JSONResponse(status_code=408 if timeout else 400, content={"request_id": request_id, "error": {
            "code": "query_timeout" if timeout else "sql_error", "sqlstate": error.sqlstate,
            "message": error.diag.message_primary, "position": error.diag.statement_position,
            "hint": error.diag.message_hint,
        }})
    except RecursionError:
        return JSONResponse(status_code=400, content={"request_id": request_id, "error": {"code": "query_too_complex", "message": "Reduce SQL nesting."}})
    finally:
        QUERY_SLOTS.release()


@app.get("/api/home")
def home(db: Database):
    return views.home(db)


def found(record):
    if record is None:
        raise HTTPException(404, "Record not found")
    return record


@app.get("/api/person")
def person(db: Database, id: RecordId):
    return found(views.person(db, id))


@app.get("/api/initiative")
def initiative(db: Database, id: RecordId):
    return found(views.initiative(db, id))


@app.get("/api/node")
def node(db: Database, id: RecordId):
    return found(views.node(db, id))


@app.get("/api/kind")
def kind(db: Database, id: RecordId):
    return views.kind(db, id)


@app.get("/api/reviews")
def reviews(db: Database, kind: str = Query(default="", max_length=100)):
    return views.reviews(db, kind)


@app.get("/api/overlap")
def overlap(db: Database, liaisons: bool = False, groups_only: bool = False, minimum: int = Query(default=3, ge=2, le=10), directory: bool = False):
    return views.overlap(db, liaisons, groups_only, minimum, directory)


SEARCH_MATCH = """document @@ websearch_to_tsquery('english', %(q)s)
    OR document @@ websearch_to_tsquery('simple', %(q)s)
    OR (%(literal)s AND (names ILIKE %(contains)s OR title %% %(q)s))"""


@app.get("/api/search")
def search(db: Database, q: str = Query(min_length=2, max_length=200), type: str | None = Query(default=None, max_length=100), limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0, le=100000)):
    term = q.strip()
    if len(term) < 2:
        raise HTTPException(422, "Enter at least two characters")
    if isinstance(type, str):
        types = {name.casefold(): name for name in topology(db)}
        canonical = types.get(type.strip().casefold())
        if canonical is None:
            raise HTTPException(422, {"message": "Unknown search type", "types": list(types.values())})
        type = canonical
    if isinstance(db, Snapshot):
        return db.search(term, type, limit, offset)
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    params = {"q": term, "contains": "%" + escaped + "%", "prefix": escaped + "%", "type": type, "limit": limit, "offset": offset, "literal": re.search(r'"|(?:^|\s)-|\bOR\b', term, re.IGNORECASE) is None}
    facets = views.rows(db, f"SELECT entity_type, count(*) count FROM search_document WHERE {SEARCH_MATCH} GROUP BY entity_type ORDER BY count DESC,entity_type", params)
    hits = views.rows(db, f"""SELECT entity_type,id,title,left(body,320) excerpt,url,
        ts_rank_cd(document,websearch_to_tsquery('english',%(q)s)) +
        ts_rank_cd(document,websearch_to_tsquery('simple',%(q)s)) + similarity(title,%(q)s) +
        CASE WHEN lower(title)=lower(%(q)s) THEN 10 WHEN title ILIKE %(prefix)s THEN 3 ELSE 0 END score
        FROM search_document WHERE ({SEARCH_MATCH}) AND (%(type)s::text IS NULL OR entity_type=%(type)s)
        ORDER BY score DESC,title,entity_type,id LIMIT %(limit)s OFFSET %(offset)s""", params)
    total = sum(facet["count"] for facet in facets if type is None or facet["entity_type"] == type)
    return {"query": term, "total": total, "facets": facets, "hits": hits, "limit": limit, "offset": offset}


def entity_schema(db, type):
    schema = topology(db)
    if type not in schema:
        raise HTTPException(404, "Unknown record type")
    return schema, schema[type]


@app.get("/api/record")
def record(db: Database, type: RecordId, id: RecordId):
    if isinstance(db, Snapshot):
        return db.record(type, id)
    schema, entity = entity_schema(db, type)
    row = found(views.one(db, sql.SQL("SELECT * FROM {}").format(sql.Identifier(type.lower())) + sql.SQL(" WHERE id=%s"), (id,)))
    title = views.one(db, "SELECT title FROM search_document WHERE entity_type=%s AND id=%s", (type,id))
    evidence = views.one(db, "SELECT data FROM provenance WHERE id=%s", (row["biotope_provenance_id"],))
    return {"entity_type": type, "title": title["title"], "record": row, "definition": entity, "provenance": evidence["data"]}


@app.get("/api/relations")
def relations(db: Database, type: RecordId, id: RecordId, limit: int = Query(default=30, ge=1, le=100), offset: int = Query(default=0, ge=0, le=100000)):
    if isinstance(db, Snapshot):
        return db.relations(type, id, limit, offset)
    schema, entity = entity_schema(db, type)
    queries = []
    params = []
    for name, edge in schema.items():
        if edge["represented_as"] == "edge":
            for endpoint, other in (("source", "target"), ("target", "source")):
                if edge[endpoint] == type:
                    queries.append(sql.SQL("""SELECT %s::text relation_type,r.id relation_id,%s::text direction,
                        %s::text entity_type,r.{} id,s.title FROM {} r JOIN search_document s ON s.entity_type=%s AND s.id=r.{}
                        WHERE r.{}=%s""").format(sql.Identifier(other), sql.Identifier(name.lower()), sql.Identifier(other), sql.Identifier(endpoint)))
                    params.extend([name, "outgoing" if endpoint == "source" else "incoming", edge[other], edge[other], id])
    if not queries:
        return {"total": 0, "items": [], "limit": limit, "offset": offset}
    union = sql.SQL(" UNION ALL ").join(queries)
    total = views.one(db, sql.SQL("SELECT count(*) total FROM ({}) links").format(union), params)["total"]
    items = views.rows(db, sql.SQL("SELECT * FROM ({}) links ORDER BY relation_type,title,relation_id,direction LIMIT %s OFFSET %s").format(union), [*params,limit,offset])
    return {"total": total, "items": items, "limit": limit, "offset": offset}


static = Path(os.environ.get("ATLAS_STATIC_DIR", Path(__file__).resolve().parents[2] / "dashboard" / "dist"))
if static.is_dir():
    app.mount("/", StaticFiles(directory=static, html=True), name="dashboard")
