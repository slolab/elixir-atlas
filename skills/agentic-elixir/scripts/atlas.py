import argparse
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time


ASSETS = Path(__file__).resolve().parents[1] / "assets"
MAX_BYTES = 1_000_000


def read_json(name):
    return json.loads((ASSETS / name).read_text())


def unpack(name, metadata):
    expected = metadata["files"][name]
    directory = Path(tempfile.gettempdir()) / "agentic-elixir" / expected["sha256"]
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected["sha256"]:
        return target
    source = ASSETS / (name + ".gz")
    if source.is_file():
        content = gzip.decompress(source.read_bytes())
    else:
        content = lzma.decompress((ASSETS / (name + ".xz")).read_bytes())
    if len(content) != expected["size"] or hashlib.sha256(content).hexdigest() != expected["sha256"]:
        raise ValueError(f"Bundled {name} failed its release checksum. Reinstall the skill.")
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, target)
    return target


def connect(path):
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db


def table_name(value, schema):
    names = {name.casefold(): name for name in schema}
    if value.casefold() not in names:
        raise ValueError(f"Unknown table {value}. Run schema to discover table names.")
    return names[value.casefold()]


def identifier(name):
    return '"' + name.replace('"', '""') + '"'


def authorize(action, first, second, database, trigger):
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
    return sqlite3.SQLITE_OK if action in allowed and second != "load_extension" else sqlite3.SQLITE_DENY


def query(db, sql, limit):
    deadline = time.monotonic() + 5
    db.set_authorizer(authorize)
    db.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
    cursor = db.execute(sql)
    if cursor.description is None:
        raise ValueError("Use a SELECT query that returns rows.")
    columns = [column[0] for column in cursor.description]
    rows = []
    size = len(json.dumps(columns).encode())
    reason = None
    for row in cursor:
        if len(rows) == limit:
            reason = "rows"
            break
        values = list(row)
        if any(isinstance(value, bytes) for value in values):
            raise ValueError("Binary query results are not supported. Select hex(value) or a text value instead.")
        size += len(json.dumps(values, ensure_ascii=False).encode()) + 2
        if size > MAX_BYTES - 512:
            if not rows:
                raise ValueError("The first row exceeds 1 MB. Select fewer fields or shorter values.")
            reason = "bytes"
            break
        rows.append(values)
    return {"columns": columns, "rows": rows, "row_count": len(rows), "truncated": reason is not None, "truncation_reason": reason}


def search(db, term, type, limit, offset):
    if not 2 <= len(term.strip()) <= 200:
        raise ValueError("Search requires 2–200 characters.")
    tokens = re.findall(r'"([^\"]+)"|(\w+)', term, re.UNICODE)
    match = " AND ".join('"' + (phrase or word).replace('"', '""') + '"' for phrase, word in tokens)
    if not match:
        raise ValueError("Search requires a word or quoted phrase.")
    facets = [dict(row) for row in db.execute("SELECT d.entity_type,count(*) count FROM search_fts f JOIN search_document d ON d.rowid=f.rowid WHERE search_fts MATCH ? GROUP BY d.entity_type ORDER BY count DESC,d.entity_type", (match,))]
    hits = [dict(row) for row in db.execute("SELECT d.entity_type,d.id,d.title,substr(d.body,1,320) excerpt,d.url,-bm25(search_fts,5,1) score FROM search_fts f JOIN search_document d ON d.rowid=f.rowid WHERE search_fts MATCH ? AND (? IS NULL OR d.entity_type=?) ORDER BY score DESC,d.title,d.entity_type,d.id LIMIT ? OFFSET ?", (match, type, type, limit, offset))]
    total = sum(facet["count"] for facet in facets if type is None or facet["entity_type"] == type)
    return {"query": term, "total": total, "facets": facets, "hits": hits, "limit": limit, "offset": offset, "has_more": offset + len(hits) < total}


def record(db, type, id, schema, manifest):
    row = db.execute(f"SELECT * FROM {identifier(type)} WHERE id=?", (id,)).fetchone()
    if row is None:
        raise ValueError("Record not found.")
    result = dict(row)
    for column, kind in schema[type]["properties"].items():
        if result[column] is not None:
            if kind == "str[]":
                result[column] = json.loads(result[column])
            elif kind == "bool":
                result[column] = bool(result[column])
    provenance = json.loads(unpack("provenance.json", manifest).read_text())
    entry = provenance["records"][result["biotope_provenance_id"]]
    evidence = []
    for index in entry["evidence"]:
        item = provenance["evidence"][index]
        evidence.append({**provenance["sources"][item["source"]], **{key: value for key, value in item.items() if key != "source"}})
    return {"entity_type": type, "record": result, "provenance": {"mappings": entry["mappings"], "evidence": evidence}}


def main():
    parser = argparse.ArgumentParser(description="Query the bundled ELIXIR Atlas release without network access.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("release")
    commands.add_parser("verify")
    schema_command = commands.add_parser("schema")
    schema_command.add_argument("tables", nargs="*")
    schema_command.add_argument("--full", action="store_true")
    search_command = commands.add_parser("search")
    search_command.add_argument("term")
    search_command.add_argument("--type")
    search_command.add_argument("--limit", type=int, default=30, choices=range(1, 101), metavar="1–100")
    search_command.add_argument("--offset", type=int, default=0)
    record_command = commands.add_parser("record")
    record_command.add_argument("type")
    record_command.add_argument("id")
    query_command = commands.add_parser("query")
    query_command.add_argument("sql", help="SQLite SELECT query, or - to read SQL from stdin.")
    query_command.add_argument("--limit", type=int, default=100, choices=range(1, 1001), metavar="1–1000")
    args = parser.parse_args()
    manifest = read_json("manifest.json")
    metadata = read_json("metadata.json")
    schema = read_json("schema.json")
    result = {"release": manifest["id"], "mode": "bundled", "dialect": "SQLite"}
    if args.command == "release":
        result.update(counts=metadata["counts"], manifest=manifest)
    elif args.command == "schema":
        names = [table_name(name, schema) for name in args.tables] if args.tables else list(schema)
        result["tables"] = {name: schema[name] if args.tables or args.full else {key: value for key, value in schema[name].items() if key in {"description", "represented_as", "source", "target"}} for name in names}
    elif args.command == "search":
        if args.offset < 0:
            raise ValueError("Offset must be non-negative.")
        type = table_name(args.type, schema) if args.type else None
        with connect(unpack("search.sqlite", metadata)) as db:
            result.update(search(db, args.term, type, args.limit, args.offset))
    else:
        with connect(unpack("graph.sqlite", manifest)) as db:
            if args.command == "verify":
                if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("Database integrity check failed.")
                counts = {name: db.execute(f"SELECT count(*) FROM {identifier(name)}").fetchone()[0] for name in schema}
                if counts != metadata["counts"]:
                    raise ValueError("Bundled record counts differ from the release.")
                unpack("provenance.json", manifest)
                unpack("run.json", manifest)
                schema_bytes = (ASSETS / "schema_config.yaml").read_bytes()
                if hashlib.sha256(schema_bytes).hexdigest() != manifest["files"]["schema_config.yaml"]["sha256"]:
                    raise ValueError("Bundled schema failed its release checksum.")
                with connect(unpack("search.sqlite", metadata)) as search_db:
                    if search_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or search_db.execute("SELECT count(*) FROM search_document").fetchone()[0] != sum(counts.values()):
                        raise ValueError("Search index integrity check failed.")
                result.update(status="ok", tables=len(counts), records=sum(counts.values()), counts=counts)
            elif args.command == "record":
                result.update(record(db, table_name(args.type, schema), args.id, schema, manifest))
            else:
                sql = sys.stdin.read() if args.sql == "-" else args.sql
                result.update(query(db, sql, args.limit))
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, sqlite3.Error, sqlite3.Warning) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        sys.exit(1)
