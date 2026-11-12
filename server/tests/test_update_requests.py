import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from pydantic import ValidationError

from atlas_api.import_release import import_release
from atlas_api.main import app
from atlas_api.permissions import check_reader, check_role, provision
from atlas_api.update_requests import UpdateRequest, check_database
from test_serving import fixture


class RequestValidationTests(unittest.TestCase):
    def test_invalid_submissions(self):
        for fields in (
            {"message": "   "}, {"message": "x" * 5001}, {"message": "bad\x00text"},
            {"message": "\ud800"}, {"entity_type": "Thing"}, {"entity_id": "one"},
            {"entity_type": " ", "entity_id": "one"}, {"origin": "reviewer"},
            {"status": "approved"}, {"release_id": "forged"}, {"context": "x" * 10001},
        ):
            with self.subTest(fields=str(fields)[:80]), self.assertRaises(ValidationError):
                UpdateRequest.model_validate({"origin": "agent", "message": "Incorrect name", **fields})

    def test_writer_must_be_separate_in_same_database(self):
        reader = "postgresql://reader:password@localhost:5432/atlas"
        check_database(reader, "postgresql://writer:password@localhost:5432/atlas")
        for writer in (reader, "postgresql://writer:password@localhost:5432/other"):
            with self.assertRaises(ValueError):
                check_database(reader, writer)

    def test_sqlite_is_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fixture(path)
            with patch.dict(os.environ, {"ATLAS_SQLITE_PATH": str(path / "graph.sqlite")}), TestClient(app) as client:
                self.assertFalse(client.get("/api/release").json()["api"]["update_requests"])
                response = client.post("/api/update-requests", json={"origin": "dashboard", "message": "Wrong name"})
                self.assertEqual(response.status_code, 503)


@unittest.skipUnless(os.environ.get("ATLAS_TEST_ADMIN_URL"), "Requires disposable local PostgreSQL")
class RequestDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = os.environ["ATLAS_TEST_ADMIN_URL"]
        cls.name = "atlas_requests_test_" + uuid.uuid4().hex[:10]
        cls.reader, cls.writer = cls.name + "_reader", cls.name + "_writer"
        with psycopg.connect(cls.admin, autocommit=True) as db:
            db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cls.name)))
        cls.owner_url = make_conninfo(cls.admin, dbname=cls.name)
        cls.reader_url = make_conninfo(cls.owner_url, user=cls.reader, password=uuid.uuid4().hex)
        cls.writer_url = make_conninfo(cls.owner_url, user=cls.writer, password=uuid.uuid4().hex)
        provision(cls.owner_url, cls.reader_url)
        provision(cls.owner_url, cls.writer_url, request_writer=True)
        cls.directory = tempfile.TemporaryDirectory()
        cls.path = Path(cls.directory.name)
        fixture(cls.path)
        import_release(cls.path, cls.owner_url, reader=cls.reader)
        cls.environment = patch.dict(os.environ, {"DATABASE_URL": cls.reader_url, "ATLAS_REQUEST_DATABASE_URL": cls.writer_url, "ATLAS_SQLITE_PATH": ""})
        cls.environment.start()
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        cls.environment.stop()
        with psycopg.connect(cls.admin, autocommit=True) as db:
            db.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(cls.name)))
            for role in (cls.reader, cls.writer):
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
        cls.directory.cleanup()

    def test_submission_persists_without_changing_graph(self):
        self.assertTrue(self.client.get("/api/release").json()["api"]["update_requests"])
        body = {"origin": "dashboard", "entity_type": "Thing", "entity_id": "one", "message": "  Wrong name  ", "proposed_change": "O'Brien", "evidence": "https://example.org/source", "context": "#/record/Thing/one"}
        response = self.client.post("/api/update-requests", json=body)
        self.assertEqual(response.status_code, 201, response.text)
        receipt = response.json()
        self.assertEqual(receipt["status"], "pending")
        with psycopg.connect(self.owner_url, row_factory=dict_row) as db:
            row = db.execute("SELECT * FROM atlas_feedback.update_request WHERE id=%s", (receipt["id"],)).fetchone()
            self.assertEqual(row["message"], "Wrong name")
            self.assertEqual(row["proposed_change"], "O'Brien")
            self.assertEqual(row["release_id"], "test")
            self.assertEqual(row["status"], "pending")
            self.assertIsNotNone(row["created_at"])
            self.assertEqual(db.execute("SELECT name FROM atlas.thing WHERE id='one'").fetchone()["name"], "Alpha")
        import_release(self.path, self.owner_url, reader=self.reader)
        provision(self.owner_url, self.writer_url, request_writer=True)
        with psycopg.connect(self.owner_url) as db:
            self.assertEqual(db.execute("SELECT status FROM atlas_feedback.update_request WHERE id=%s", (receipt["id"],)).fetchone()[0], "pending")
        agent = self.client.post("/api/update-requests", json={"origin": "agent", "message": "The answer confused two people", "context": "Original answer excerpt"})
        self.assertEqual(agent.status_code, 201, agent.text)

    def test_invalid_targets_and_public_boundaries(self):
        base = {"origin": "agent", "message": "Wrong name"}
        for fields, expected in (({"entity_type": "Thing", "entity_id": "missing"}, 404), ({"entity_type": "Missing", "entity_id": "one"}, 404), ({"status": "approved"}, 422), ({"message": " "}, 422)):
            response = self.client.post("/api/update-requests", json={**base, **fields})
            self.assertEqual(response.status_code, expected, response.text)
        for method in ("get", "patch", "delete"):
            self.assertIn(getattr(self.client, method)("/api/update-requests").status_code, (404, 405))
        response = self.client.post("/api/query", json={"sql": "SELECT * FROM atlas_feedback.update_request"})
        self.assertEqual(response.status_code, 400)

    def test_database_permissions_enforce_sink(self):
        forbidden = [
            "UPDATE atlas.thing SET name='changed'", "DELETE FROM atlas.thing",
            "UPDATE atlas_feedback.update_request SET status='approved'",
            "DELETE FROM atlas_feedback.update_request", "TRUNCATE atlas_feedback.update_request",
            "SELECT * FROM atlas_feedback.update_request",
            "INSERT INTO atlas_feedback.update_request (status) VALUES ('approved')",
            "CREATE TABLE public.changed (id int)", "SET ROLE postgres",
        ]
        for statement in forbidden:
            with self.subTest(statement=statement), psycopg.connect(self.writer_url) as db:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    db.execute(statement)
        with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
            db.execute("SET TRANSACTION READ WRITE")
            check_reader(db)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                db.execute("INSERT INTO atlas_feedback.update_request (message) VALUES ('changed')")
        with psycopg.connect(self.writer_url, row_factory=dict_row) as db:
            check_role(db, request_writer=True)
            with self.assertRaises(RuntimeError):
                check_reader(db)
        with psycopg.connect(self.owner_url, row_factory=dict_row) as db:
            with self.assertRaises(RuntimeError):
                check_role(db, request_writer=True)

    def test_startup_rejects_extra_privileges(self):
        for privilege in ("INSERT (status)", "SELECT", "SELECT (message)"):
            with psycopg.connect(self.owner_url) as db:
                db.execute(sql.SQL("GRANT " + privilege + " ON atlas_feedback.update_request TO {}").format(sql.Identifier(self.writer)))
            try:
                with self.subTest(privilege=privilege), psycopg.connect(self.writer_url, row_factory=dict_row) as db:
                    with self.assertRaises(RuntimeError):
                        check_role(db, request_writer=True)
            finally:
                with psycopg.connect(self.owner_url) as db:
                    db.execute(sql.SQL("REVOKE " + privilege + " ON atlas_feedback.update_request FROM {}").format(sql.Identifier(self.writer)))

    def test_failed_write_does_not_report_success(self):
        with patch("atlas_api.main.insert_request", side_effect=psycopg.OperationalError("Unavailable")):
            response = self.client.post("/api/update-requests", json={"origin": "dashboard", "message": "Wrong name"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("id", response.json())
