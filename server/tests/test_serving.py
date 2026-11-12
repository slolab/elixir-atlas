import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
import uuid
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg
import yaml
from psycopg import sql
from psycopg.rows import dict_row

from atlas_api import views
from atlas_api.import_release import import_release, verify_release
from atlas_api.main import record, relations, search
from atlas_api.schema import ddl, identifier, read_schema


def fixture(path, invalid=False):
    schema = {
        "Thing": {"represented_as": "node", "properties": {"name": "str", "aliases": "str[]", "active": "bool", "score": "float", "optional": "str", "biotope_provenance_id": "int"}, "biotope": {"nullable": ["optional"]}},
        "Link": {"represented_as": "edge", "source": "Thing", "target": "Thing", "properties": {"biotope_provenance_id": "int"}, "biotope": {"nullable": []}},
    }
    (path / "schema_config.yaml").write_text(yaml.safe_dump(schema))
    (path / "provenance.json").write_text(json.dumps({"sources": [{"artifact": "source.csv", "version": "sha256:test"}], "evidence": [{"source": 0, "location": "row 1"}], "records": [{"mappings": ["thing"], "evidence": [0]}]}))
    (path / "run.json").write_text("{}")
    database = path / "graph.sqlite"
    if database.exists():
        database.unlink()
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("CREATE TABLE Thing (id TEXT PRIMARY KEY,name TEXT,aliases TEXT,active INTEGER,score REAL,optional TEXT,biotope_provenance_id INTEGER)")
        conn.execute("INSERT INTO Thing VALUES ('one','Alpha','[\"First\"]',1,1.5,NULL,0)")
        conn.execute("CREATE TABLE Link (id TEXT PRIMARY KEY,source TEXT,target TEXT,biotope_provenance_id INTEGER)")
        conn.execute("INSERT INTO Link VALUES ('link','one',?,0)", ("missing" if invalid else "one",))
    manifest = {"id": "invalid" if invalid else "test", "files": {}}
    for filename in ("graph.sqlite", "schema_config.yaml", "provenance.json", "run.json"):
        content = (path / filename).read_bytes()
        manifest["files"][filename] = {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
    (path / "manifest.json").write_text(json.dumps(manifest))


class SchemaTests(unittest.TestCase):
    def test_schema_types_and_constraints(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fixture(path)
            generated = ddl(read_schema(path / "schema_config.yaml"))
            self.assertIn('"aliases" text[] NOT NULL', generated)
            self.assertIn('"active" boolean NOT NULL', generated)
            self.assertIn('"optional" text,', generated)
            self.assertIn('REFERENCES "atlas"."thing"(id)', generated)
            self.assertLess(generated.index('CREATE TABLE "atlas"."thing"'), generated.index('CREATE TABLE "atlas"."link"'))

    def test_bad_identifier_and_type_fail(self):
        with self.assertRaises(ValueError):
            identifier('thing; DROP TABLE person')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fixture(path)
            target = path / "schema_config.yaml"
            target.write_text(target.read_text().replace("str[]", "mystery"))
            with self.assertRaises(ValueError):
                read_schema(target)

    def test_checksum_fails_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fixture(path)
            verify_release(path)
            (path / "run.json").write_text('{"changed":true}')
            with self.assertRaises(ValueError):
                verify_release(path)


@unittest.skipUnless(os.environ.get("DATABASE_ADMIN_URL"), "Requires PostgreSQL owner credentials")
class ImportTests(unittest.TestCase):
    def test_typed_import_repeat_and_rollback(self):
        namespace = "atlas_test_" + uuid.uuid4().hex[:12]
        url = os.environ["DATABASE_ADMIN_URL"]
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                fixture(path)
                for _ in range(2):
                    self.assertEqual(import_release(path, url, namespace)["records"], 2)
                with psycopg.connect(url) as conn:
                    row = conn.execute(sql.SQL("SELECT aliases,active,score,optional FROM {}.thing").format(sql.Identifier(namespace))).fetchone()
                    self.assertEqual(row, (["First"], True, 1.5, None))
                fixture(path, invalid=True)
                with self.assertRaises((psycopg.errors.ForeignKeyViolation, KeyError)):
                    import_release(path, url, namespace)
                with psycopg.connect(url) as conn:
                    self.assertEqual(conn.execute(sql.SQL("SELECT id FROM {}.release").format(sql.Identifier(namespace))).fetchone()[0], "test")
        finally:
            with psycopg.connect(url) as conn:
                conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(namespace)))


@unittest.skipUnless(os.environ.get("DATABASE_URL") and os.environ.get("ATLAS_RELEASE_DIR"), "Requires imported release")
class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.connection = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
        self.connection.execute("SET TRANSACTION READ ONLY")
        self.connection.execute("SET LOCAL search_path TO atlas,public")

    def tearDown(self):
        self.connection.close()

    def test_every_source_row_and_column_roundtrips(self):
        path = Path(os.environ["ATLAS_RELEASE_DIR"])
        schema = read_schema(path / "schema_config.yaml")
        total = 0
        from atlas_api.import_release import converted
        with closing(sqlite3.connect(f"file:{path / 'graph.sqlite'}?mode=ro", uri=True)) as source:
            source.row_factory = sqlite3.Row
            for name, entity in schema.items():
                expected = [converted(row, entity) for row in source.execute(f"SELECT * FROM {identifier(name)} ORDER BY id")]
                actual = self.connection.execute(sql.SQL("SELECT * FROM {} ORDER BY id").format(sql.Identifier(name.lower()))).fetchall()
                self.assertEqual({row["id"]: row for row in actual}, {row["id"]: row for row in expected}, name)
                total += len(expected)
        self.assertEqual(self.connection.execute("SELECT count(*) n FROM search_document").fetchone()["n"], total)

    def test_all_dashboard_views(self):
        conn = self.connection
        home = views.home(conn)
        self.assertTrue(home["nodes"])
        self.assertTrue(home["projects"])
        person_id = views.one(conn, "SELECT source FROM HoldsRole GROUP BY source ORDER BY count(*) DESC LIMIT 1")["source"]
        self.assertTrue(views.person(conn, person_id)["roles"])
        initiative_id = views.one(conn, "SELECT target FROM HoldsRole GROUP BY target ORDER BY count(*) DESC LIMIT 1")["target"]
        self.assertTrue(views.initiative(conn, initiative_id)["roles"])
        self.assertIsNotNone(views.node(conn, home["nodes"][0]["id"]))
        self.assertTrue(views.kind(conn, home["kinds"][0]["kind"]))
        self.assertTrue(views.reviews(conn, "")["items"])
        for liaisons in (False, True):
            for groups in (False, True):
                self.assertIn("holders", views.overlap(conn, liaisons, groups, 3))
        self.assertIsNone(views.person(conn, "missing"))

    def test_search_paging_filters_phrases_and_injection(self):
        conn = self.connection
        first = search(conn, "FAIR", None, 5, 0)
        second = search(conn, "FAIR", None, 5, 5)
        self.assertGreater(first["total"], 5)
        self.assertFalse({(h["entity_type"], h["id"]) for h in first["hits"]} & {(h["entity_type"], h["id"]) for h in second["hits"]})
        filtered = search(conn, "FAIR", "Initiative", 5, 0)
        self.assertTrue(all(hit["entity_type"] == "Initiative" for hit in filtered["hits"]))
        self.assertEqual(sum(f["count"] for f in first["facets"]), first["total"])
        self.assertEqual(search(conn, '"zzzzinvented unlikelyphrase"', None, 5, 0)["total"], 0)
        self.assertEqual(search(conn, "'; DROP TABLE person; --", None, 5, 0)["total"], 0)
        self.assertGreater(views.one(conn, "SELECT count(*) n FROM person")["n"], 0)

    def test_generic_records_and_provenance(self):
        conn = self.connection
        for entry in views.rows(conn, "SELECT DISTINCT ON (entity_type) entity_type,id FROM search_document ORDER BY entity_type,id"):
            result = record(conn, entry["entity_type"], entry["id"])
            self.assertEqual(result["record"]["id"], entry["id"])
            self.assertIn("evidence", result["provenance"])
            links = relations(conn, entry["entity_type"], entry["id"], 5, 0)
            self.assertLessEqual(len(links["items"]), 5)

    def test_search_plan_uses_indexes(self):
        conn = self.connection
        conn.execute("SET LOCAL enable_seqscan=off")
        plan = conn.execute("EXPLAIN (FORMAT JSON) SELECT id FROM search_document WHERE document @@ websearch_to_tsquery('english','genomics')").fetchone()
        self.assertIn("Bitmap Index Scan", json.dumps(plan))


@unittest.skipUnless(os.environ.get("ATLAS_TEST_BASE_URL"), "Requires running API")
class HttpTests(unittest.TestCase):
    def test_public_api_boundaries(self):
        base = os.environ["ATLAS_TEST_BASE_URL"]
        for path in ("/healthz", "/api/home", "/api/schema", "/api/release", "/openapi.json", "/"):
            with urlopen(base + path, timeout=20) as response:
                self.assertEqual(response.status, 200)
        for path, status in (("/api/search?q=a", 422), ("/api/search?q=FAIR&limit=1000", 422), ("/api/record?type=Unknown&id=test", 404), ("/api/person?id=missing", 404), ("/graph.sqlite", 404), ("/api/sql", 404)):
            with self.assertRaises(HTTPError) as context:
                urlopen(base + path, timeout=20)
            self.assertEqual(context.exception.code, status, path)
        with self.assertRaises(HTTPError) as context:
            urlopen(Request(base + "/api/search?" + urlencode({"q": "FAIR"}), data=b"{}", method="POST"), timeout=20)
        self.assertEqual(context.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
