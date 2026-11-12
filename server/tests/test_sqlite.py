import hashlib
import importlib.util
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from atlas_api import views
from atlas_api.main import app
from atlas_api.sqlite_snapshot import Snapshot
from test_serving import fixture


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        fixture(self.path)
        self.database = self.path / "graph.sqlite"
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("DROP TABLE Link")
            db.execute("CREATE TABLE Link (id TEXT PRIMARY KEY,source TEXT REFERENCES Thing(id),target TEXT REFERENCES Thing(id),biotope_provenance_id INTEGER)")
            db.execute("INSERT INTO Link VALUES ('link','one','one',0)")
            db.execute("INSERT INTO Thing VALUES ('two','Alpha beta','[\"Second\"]',0,2,NULL,0)")

    def test_bare_snapshot_is_unchanged_and_read_only(self):
        (self.path / "schema_config.yaml").unlink()
        (self.path / "provenance.json").unlink()
        before = hashlib.sha256(self.database.read_bytes()).hexdigest()
        with closing(Snapshot(self.database)) as db:
            record = db.record("Thing", "one")
            self.assertEqual(record["record"]["aliases"], ["First"])
            self.assertFalse(record["provenance"]["available"])
            self.assertEqual(record["definition"]["biotope"]["property_descriptions"], {})
            self.assertEqual(db.schema["Link"]["source"], "Thing")
            links = db.relations("Thing", "one", 10, 0)
            self.assertEqual(links["total"], 2)
            self.assertEqual({item["direction"] for item in links["items"]}, {"incoming", "outgoing"})
            self.assertEqual(views.one(db, "SELECT name FROM Thing WHERE id=%s", ("one",))["name"], "Alpha")
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("DELETE FROM Thing")
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).hexdigest(), before)

    def test_metadata_and_indexed_search(self):
        with closing(Snapshot(self.database)) as db:
            record = db.record("Thing", "one")
            self.assertIs(record["record"]["active"], True)
            self.assertEqual(record["provenance"]["evidence"][0]["artifact"], "source.csv")
            result = db.search("Alpha", "Thing", 1, 0)
            self.assertEqual(result["total"], 2)
            self.assertEqual(result["hits"][0]["id"], "one")
            self.assertEqual(db.search("Alpha", "Thing", 1, 1)["hits"][0]["id"], "two")
            self.assertEqual(db.search('"Alpha beta"', "Thing", 10, 0)["total"], 1)
            self.assertEqual(db.search("First", "Thing", 10, 0)["hits"][0]["id"], "one")
            self.assertEqual(db.search("'; DROP TABLE Thing; --", None, 10, 0)["total"], 0)
            self.assertEqual(db.search("---", None, 10, 0)["hits"], [])
            self.assertEqual(sum(row["count"] for row in result["facets"]), db.search("Alpha", None, 10, 0)["total"])
            plan = db.execute("EXPLAIN QUERY PLAN SELECT rowid FROM search_fts WHERE search_fts MATCH ?", ('"Alpha"',)).fetchall()
            self.assertIn("VIRTUAL TABLE INDEX", str(plan))

    @unittest.skipUnless(importlib.util.find_spec("httpx"), "Requires the server dev dependencies")
    def test_http_mode_selection_and_boundaries(self):
        from fastapi.testclient import TestClient

        with patch.dict(os.environ, {"ATLAS_SQLITE_PATH": str(self.database), "DATABASE_URL": "unused"}), TestClient(app) as client:
            self.assertEqual(client.get("/healthz").json()["mode"], "sqlite")
            self.assertEqual(client.get("/api/release").json()["counts"]["Thing"], 2)
            self.assertEqual(client.get("/api/schema").json()["Thing"]["represented_as"], "node")
            for path, status in (
                ("/api/search?q=Alpha&type=Thing", 200),
                ("/api/record?type=Thing&id=one", 200),
                ("/api/relations?type=Thing&id=one", 200),
                ("/api/record?type=Thing&id=missing", 404),
                ("/api/record?type=Unknown&id=one", 404),
                ("/api/search?q=a", 422),
                ("/api/search?q=Alpha&limit=1000", 422),
                ("/graph.sqlite", 404),
                ("/api/sql", 404),
            ):
                self.assertEqual(client.get(path).status_code, status, path)
            self.assertEqual(client.post("/api/search?q=Alpha").status_code, 405)

    def test_missing_snapshot_does_not_create_file(self):
        missing = self.path / "missing.sqlite"
        with self.assertRaises(FileNotFoundError):
            Snapshot(missing)
        self.assertFalse(missing.exists())


@unittest.skipUnless(os.environ.get("ATLAS_TEST_SQLITE"), "Requires a built Atlas snapshot")
class BuiltSnapshotTests(unittest.TestCase):
    def test_all_views_and_record_types(self):
        with closing(Snapshot(os.environ["ATLAS_TEST_SQLITE"])) as db:
            home = views.home(db)
            self.assertTrue(home["nodes"])
            self.assertTrue(home["projects"])
            person_id = views.one(db, "SELECT source FROM HoldsRole GROUP BY source ORDER BY count(*) DESC LIMIT 1")["source"]
            self.assertTrue(views.person(db, person_id)["roles"])
            initiative_id = views.one(db, "SELECT target FROM HoldsRole GROUP BY target ORDER BY count(*) DESC LIMIT 1")["target"]
            self.assertTrue(views.initiative(db, initiative_id)["roles"])
            self.assertTrue(views.node(db, home["nodes"][0]["id"]))
            self.assertTrue(views.kind(db, home["kinds"][0]["kind"]))
            self.assertTrue(views.reviews(db, "")["items"])
            for liaisons in (False, True):
                for groups_only in (False, True):
                    self.assertTrue(views.overlap(db, liaisons, groups_only, 3)["holders"])
            for type in db.schema:
                entry = db.execute("SELECT id FROM search_document WHERE entity_type=? LIMIT 1", (type,)).fetchone()
                if entry:
                    self.assertEqual(db.record(type, entry["id"])["record"]["id"], entry["id"])
                    self.assertLessEqual(len(db.relations(type, entry["id"], 5, 0)["items"]), 5)
            self.assertGreater(db.search("Bioschemas", "Initiative", 5, 0)["total"], 0)
