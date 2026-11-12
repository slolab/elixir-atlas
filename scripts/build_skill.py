import argparse
import gzip
import hashlib
import json
import lzma
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from atlas_api.import_release import converted, search_record, title_for, verify_release
from atlas_api.schema import identifier, ordered_tables, read_schema


def build_search(release, schema, destination):
    counts, titles = {}, {}
    with closing(sqlite3.connect((release / "graph.sqlite").as_uri() + "?mode=ro", uri=True)) as source, closing(sqlite3.connect(destination)) as search:
        source.row_factory = sqlite3.Row
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or source.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Release SQLite integrity check failed")
        actual = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if actual != set(schema):
            raise ValueError("Release schema and SQLite tables differ")
        search.execute("CREATE TABLE search_document (entity_type TEXT,id TEXT,title TEXT,names TEXT,body TEXT,url TEXT,PRIMARY KEY(entity_type,id))")
        for name in ordered_tables(schema):
            entity = schema[name]
            cursor = source.execute(f"SELECT * FROM {identifier(name)} ORDER BY id")
            expected = {"id", *entity["properties"]} | ({"source", "target"} if entity["represented_as"] == "edge" else set())
            if {column[0] for column in cursor.description} != expected:
                raise ValueError(f"Release columns differ: {name}")
            records = [converted(row, entity) for row in cursor]
            counts[name] = len(records)
            if entity["represented_as"] == "node":
                titles.update({(name, row["id"]): title_for(row) for row in records})
            search.executemany("INSERT INTO search_document VALUES (?,?,?,?,?,?)", (search_record(name, row, entity, titles) for row in records))
        search.execute("CREATE VIRTUAL TABLE search_fts USING fts5(names,body,content='',tokenize='porter unicode61')")
        search.execute("INSERT INTO search_fts(rowid,names,body) SELECT rowid,names,body FROM search_document")
        search.execute("INSERT INTO search_fts(search_fts) VALUES ('optimize')")
        search.execute("UPDATE search_document SET body=substr(body,1,320)")
        search.commit()
        search.execute("VACUUM")
        if search.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Search SQLite integrity check failed")
        if search.execute("SELECT count(*) FROM search_document").fetchone()[0] != sum(counts.values()):
            raise ValueError("Search record count differs from release")
        if search.execute("SELECT count(*) FROM search_fts").fetchone()[0] != sum(counts.values()):
            raise ValueError("Full-text index count differs from release")
    return counts


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def build(release, output):
    release, output = release.resolve(), output.resolve()
    if output.suffix != ".zip":
        raise ValueError("Output must have a .zip extension")
    manifest = verify_release(release)
    schema = read_schema(release / "schema_config.yaml")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="atlas-skill-", dir=output.parent) as temporary:
        temporary = Path(temporary)
        package = temporary / "agentic-elixir"
        shutil.copytree(ROOT / "skills" / "agentic-elixir", package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "assets"))
        assets = package / "assets"
        assets.mkdir()
        shutil.copy2(release / "manifest.json", assets / "manifest.json")
        shutil.copy2(release / "schema_config.yaml", assets / "schema_config.yaml")
        write_json(assets / "schema.json", schema)
        for filename in ("graph.sqlite", "provenance.json", "run.json"):
            (assets / f"{filename}.gz").write_bytes(gzip.compress((release / filename).read_bytes(), compresslevel=9, mtime=0))
        search_path = temporary / "search.sqlite"
        counts = build_search(release, schema, search_path)
        search_bytes = search_path.read_bytes()
        (assets / "search.sqlite.xz").write_bytes(lzma.compress(search_bytes, preset=6))
        metadata = {"release": manifest["id"], "counts": counts, "files": {"search.sqlite": {
            "sha256": hashlib.sha256(search_bytes).hexdigest(), "size": len(search_bytes),
        }}}
        write_json(assets / "metadata.json", metadata)
        files = sorted(path for path in package.rglob("*") if path.is_file())
        size = sum(path.stat().st_size for path in files)
        if size > 30_000_000:
            raise ValueError(f"Skill files total {size:,} bytes, exceeding the 30 MB upload budget")
        archive = temporary / output.name
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for path in files:
                bundle.write(path, Path("agentic-elixir") / path.relative_to(package), compress_type=zipfile.ZIP_STORED if path.suffix in {".gz", ".xz"} else zipfile.ZIP_DEFLATED)
        unpacked = output.with_suffix("")
        if unpacked.exists():
            shutil.rmtree(unpacked)
        shutil.move(str(package), unpacked)
        archive.replace(output)
    return {"release": manifest["id"], "tables": len(counts), "records": sum(counts.values()), "files_bytes": size, "zip_bytes": output.stat().st_size, "archive": str(output), "unpacked": str(unpacked)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "agentic-elixir.zip")
    args = parser.parse_args()
    print(json.dumps(build(args.release, args.output)))


if __name__ == "__main__":
    main()
