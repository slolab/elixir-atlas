import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from .schema import ddl, identifier, ordered_tables, read_schema
from .permissions import grant_reader


def verify_release(path):
    manifest = json.loads((path / "manifest.json").read_text())
    for filename in ("graph.sqlite", "schema_config.yaml", "provenance.json", "run.json"):
        metadata = manifest["files"][filename]
        content = (path / filename).read_bytes()
        if len(content) != metadata["size"] or hashlib.sha256(content).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Release checksum mismatch: {filename}")
    return manifest


def converted(row, entity):
    result = dict(row)
    for column, kind in entity["properties"].items():
        value = result[column]
        if value is not None:
            if kind == "str[]":
                value = json.loads(value)
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    raise ValueError(f"Invalid text array: {column}")
            elif kind == "bool":
                if value not in (0, 1):
                    raise ValueError(f"Invalid boolean: {column}")
                value = bool(value)
        result[column] = value
    return result


def title_for(row):
    return next((str(row[field]) for field in ("name", "title", "label", "question", "path", "id") if row.get(field)), row["id"])


def search_record(name, row, entity, titles):
    title = title_for(row)
    if entity["represented_as"] == "edge":
        source = titles[(entity["source"], row["source"])]
        target = titles[(entity["target"], row["target"])]
        title = f"{source} — {row.get('role') or name} — {target}"
    aliases = [row.get(field) for field in ("acronym", "aliases", "name_variants", "keywords")]
    names = " ".join([title] + [" ".join(value) if isinstance(value, list) else str(value) for value in aliases if value])
    excluded = {"id", "source", "target", "biotope_provenance_id", "source_document", "path", "url", "source_url", "retrieved_at"}
    body = " ".join(" ".join(value) if isinstance(value, list) else value for field, value in row.items() if field not in excluded and isinstance(value, (str, list)))
    url = row.get("url") or row.get("source_url") or next(iter(row.get("pages") or []), None)
    return name, row["id"], title, names, body, url


def import_release(path, database_url, namespace="atlas", reader=None):
    identifier(namespace)
    staging = namespace + "_loading"
    manifest = verify_release(path)
    schema = read_schema(path / "schema_config.yaml")
    provenance = json.loads((path / "provenance.json").read_text())
    counts = {}
    titles = {}
    documents = []
    with closing(sqlite3.connect(f"file:{path / 'graph.sqlite'}?mode=ro", uri=True)) as source:
        source.row_factory = sqlite3.Row
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or source.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("SQLite integrity check failed")
        actual = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if actual != set(schema):
            raise ValueError("Release schema and SQLite tables differ")
        with psycopg.connect(database_url) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("atlas-import:" + namespace,))
            connection.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(staging)))
            connection.execute(ddl(schema, staging))
            with connection.cursor().copy(sql.SQL("COPY {}.provenance (id, data) FROM STDIN").format(sql.Identifier(staging))) as copy:
                for index, record in enumerate(provenance["records"]):
                    evidence = []
                    for evidence_id in record["evidence"]:
                        entry = provenance["evidence"][evidence_id]
                        evidence.append({**provenance["sources"][entry["source"]], **{k: v for k, v in entry.items() if k != "source"}})
                    copy.write_row((index, Jsonb({"mappings": record["mappings"], "evidence": evidence})))
            for name in ordered_tables(schema):
                entity = schema[name]
                cursor = source.execute(f"SELECT * FROM {identifier(name)} ORDER BY id")
                columns = [column[0] for column in cursor.description]
                expected = {"id", *entity["properties"]} | ({"source", "target"} if entity["represented_as"] == "edge" else set())
                if set(columns) != expected:
                    raise ValueError(f"Release columns differ: {name}")
                command = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(sql.Identifier(staging), sql.Identifier(name.lower()), sql.SQL(", ").join(map(sql.Identifier, columns)))
                count = 0
                with connection.cursor().copy(command) as copy:
                    for raw in cursor:
                        row = converted(raw, entity)
                        copy.write_row(tuple(row[column] for column in columns))
                        count += 1
                        if entity["represented_as"] == "node":
                            titles[(name, row["id"])] = title_for(row)
                        documents.append(search_record(name, row, entity, titles))
                counts[name] = count
                imported = connection.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(staging), sql.Identifier(name.lower()))).fetchone()[0]
                if imported != count:
                    raise ValueError(f"Import count mismatch: {name}")
            with connection.cursor().copy(sql.SQL("COPY {}.search_document (entity_type, id, title, names, body, url) FROM STDIN").format(sql.Identifier(staging))) as copy:
                for document in documents:
                    copy.write_row(document)
            connection.execute(sql.SQL("INSERT INTO {}.release (id, manifest, topology, counts) VALUES (%s, %s, %s, %s)").format(sql.Identifier(staging)), (manifest["id"], Jsonb(manifest), Jsonb(schema), Jsonb(counts)))
            for table in [*map(str.lower, schema), "search_document"]:
                connection.execute(sql.SQL("ANALYZE {}.{}").format(sql.Identifier(staging), sql.Identifier(table)))
            if reader:
                grant_reader(connection, staging, reader)
            connection.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(namespace)))
            connection.execute(sql.SQL("ALTER SCHEMA {} RENAME TO {}").format(sql.Identifier(staging), sql.Identifier(namespace)))
    return {"release": manifest["id"], "tables": len(counts), "records": sum(counts.values()), "counts": counts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args()
    if args.schema_only:
        print("CREATE EXTENSION IF NOT EXISTS pg_trgm;\n" + ddl(read_schema(args.release / "schema_config.yaml")))
    else:
        from psycopg.conninfo import conninfo_to_dict
        reader = conninfo_to_dict(os.environ["DATABASE_URL"])["user"]
        print(json.dumps(import_release(args.release.resolve(), os.environ["DATABASE_ADMIN_URL"], reader=reader), indent=2))


if __name__ == "__main__":
    main()
