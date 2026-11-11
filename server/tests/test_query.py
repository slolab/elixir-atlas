import json
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

from atlas_api import query
from atlas_api.import_release import import_release
from atlas_api.main import app
from atlas_api.permissions import check_reader, provision
from test_serving import fixture


class ValidationTests(unittest.TestCase):
    def test_analytical_sql(self):
        for statement in [
            "SELECT count(DISTINCT id) FILTER (WHERE name ILIKE '%a%') FROM thing",
            "WITH x AS (SELECT * FROM thing), y AS (SELECT id FROM x) SELECT * FROM y",
            "SELECT t.id, u.value FROM atlas.thing t CROSS JOIN LATERAL unnest(t.aliases) WITH ORDINALITY AS u(value, position)",
            "SELECT u.* FROM unnest(ARRAY['a']) WITH ORDINALITY u",
            "SELECT date '2026-11-11' - interval '12 months', extract(year FROM current_date), coalesce(null, 1)",
            "SELECT aliases[1], row_number() OVER (ORDER BY id) FROM thing",
            "SELECT * FROM thing WHERE NOT EXISTS (SELECT 1 FROM link WHERE target=thing.id)",
            "SELECT 1 UNION ALL SELECT 2",
        ]:
            with self.subTest(statement=statement):
                query.validate(statement, {"thing", "link"})

    def test_rejects_writes_and_nonpublic_sql(self):
        for statement in [
            "DELETE FROM thing", "SELECT 1; SELECT 2", "SELECT * INTO other FROM thing",
            "WITH x AS (DELETE FROM thing RETURNING *) SELECT * FROM x",
            "SELECT * FROM thing FOR UPDATE", "COPY thing TO STDOUT", "SET ROLE postgres",
            "SELECT * FROM pg_catalog.pg_roles", "SELECT * FROM pg_roles", "SELECT * FROM secret.thing",
            "WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles",
            "WITH x AS (SELECT * FROM pg_roles), pg_roles AS (SELECT * FROM thing) SELECT * FROM x",
            "SELECT pg_catalog.set_config('search_path','public',false)",
            "SELECT pg_advisory_lock(123)", "SELECT (123::bigint).pg_advisory_lock",
            "SELECT (1::float8).pg_sleep", "SELECT ('search_path'::text).current_setting",
            "SELECT x.current_setting FROM unnest(ARRAY['search_path']) x",
            "SELECT x.current_setting FROM unnest(ARRAY['search_path']) x(value)",
            "SELECT x.pg_sleep FROM unnest(ARRAY[1::float8]) x(value), (SELECT 1 AS pg_sleep) y",
            "SELECT (SELECT x.pg_sleep) FROM unnest(ARRAY[1::float8]) x(value)",
            "SELECT * FROM thing ORDER BY id USING OPERATOR(public.<)",
            "SELECT 'thing'::regclass", "SELECT 'x'::public.custom", "SELECT public.lower('x')",
            "SELECT query_to_xml('SELECT 1',true,true,'')",
            "SELECT * FROM thing TABLESAMPLE SYSTEM(10)",
        ]:
            with self.subTest(statement=statement), self.assertRaises(query.QueryError):
                query.validate(statement, {"thing", "link"})


    def test_rejects_invalid_text(self):
        for statement in ["SELECT 1\x00; DELETE FROM thing", "SELECT '\ud800'"]:
            with self.subTest(statement=repr(statement)), self.assertRaises(query.QueryError) as error:
                query.validate(statement, {"thing"})
            self.assertEqual(error.exception.code, "invalid_sql_text")


@unittest.skipUnless(os.environ.get("ATLAS_TEST_ADMIN_URL"), "Requires disposable local PostgreSQL")
class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = os.environ["ATLAS_TEST_ADMIN_URL"]
        cls.name = "atlas_query_test_" + uuid.uuid4().hex[:10]
        cls.reader = cls.name + "_reader"
        with psycopg.connect(cls.admin, autocommit=True) as db:
            db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cls.name)))
        cls.owner_url = make_conninfo(cls.admin, dbname=cls.name)
        cls.reader_url = make_conninfo(cls.owner_url, user=cls.reader, password=uuid.uuid4().hex)
        provision(cls.owner_url, cls.reader_url)
        cls.directory = tempfile.TemporaryDirectory()
        cls.path = Path(cls.directory.name)
        fixture(cls.path)
        for _ in range(2):
            import_release(cls.path, cls.owner_url, reader=cls.reader)
        fixture(cls.path, invalid=True)
        try:
            import_release(cls.path, cls.owner_url, reader=cls.reader)
        except (psycopg.errors.ForeignKeyViolation, KeyError):
            pass
        else:
            raise AssertionError("Invalid import succeeded")
        with psycopg.connect(cls.owner_url) as db:
            db.execute("CREATE SCHEMA private")
            db.execute("CREATE TABLE private.canary (value text)")
            db.execute("INSERT INTO private.canary VALUES ('unchanged')")
        cls.environment = patch.dict(os.environ, {"DATABASE_URL": cls.reader_url, "ATLAS_TRACE_DIR": str(cls.path / "traces")})
        cls.environment.start()
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        cls.environment.stop()
        with psycopg.connect(cls.admin, autocommit=True) as db:
            db.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(cls.name)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(cls.reader)))
        cls.directory.cleanup()

    def post(self, statement, **kwargs):
        return self.client.post("/api/query", json={"sql": statement, **kwargs})

    def test_reader_cannot_write_even_in_read_write_transaction(self):
        for statement in [
            "INSERT INTO atlas.thing (id) VALUES ('injected')", "UPDATE atlas.thing SET name='changed'",
            "DELETE FROM atlas.thing", "TRUNCATE atlas.thing", "DROP TABLE atlas.link",
            "ALTER TABLE atlas.thing ADD COLUMN changed text", "CREATE TABLE public.changed (id int)",
            "CREATE TEMP TABLE changed (id int)", "SET ROLE postgres", "SELECT * FROM private.canary",
        ]:
            with self.subTest(statement=statement), psycopg.connect(self.reader_url) as db:
                db.execute("SET TRANSACTION READ WRITE")
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    db.execute(statement)
        with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
            check_reader(db)
            self.assertEqual(db.execute("SELECT name FROM atlas.thing").fetchone()["name"], "Alpha")
        with psycopg.connect(self.owner_url, row_factory=dict_row) as db:
            with self.assertRaises(RuntimeError):
                check_reader(db)

    def test_schema_matches_imported_release(self):
        response = self.client.get("/api/schema?format=sql")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["release"], "test")
        self.assertEqual(schema["tables"]["atlas.link"]["columns"]["target"]["references"], "atlas.thing.id")
        self.assertEqual(schema["tables"]["atlas.thing"]["columns"]["aliases"]["type"], "text[]")
        self.assertTrue(schema["tables"]["atlas.thing"]["columns"]["optional"]["nullable"])
        self.assertEqual(len(schema["api_revision"]), 64)
        selected = self.client.get("/api/schema?format=sql&tables=atlas.link,thing").json()
        self.assertEqual(set(selected["tables"]), {"atlas.link", "atlas.thing"})
        self.assertEqual(selected["tables"]["atlas.thing"], schema["tables"]["atlas.thing"])
        summary = self.client.get("/api/schema?format=sql&detail=summary").json()
        self.assertNotIn("columns", summary["tables"]["atlas.link"])
        self.assertEqual(summary["tables"]["atlas.link"]["references"]["source"], "atlas.thing.id")
        self.assertEqual(self.client.get("/api/schema?format=sql&tables=private.canary").status_code, 422)

    def test_search_type_casing_and_invalid_types(self):
        canonical = self.client.get("/api/search?q=Alpha&type=Thing").json()
        for spelling in ("thing", "THING"):
            result = self.client.get("/api/search", params={"q": "Alpha", "type": spelling})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json(), canonical)
            self.assertEqual(result.json()["total"], 1)
        result = self.client.get("/api/search?q=Alpha&type=not_a_type")
        self.assertEqual(result.status_code, 422)
        self.assertIn("Thing", result.json()["detail"]["types"])

    def test_startup_detects_column_grants_and_privileged_functions(self):
        with psycopg.connect(self.owner_url) as db:
            db.execute(sql.SQL("GRANT UPDATE(name) ON atlas.thing TO {}").format(sql.Identifier(self.reader)))
        try:
            with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
                with self.assertRaises(RuntimeError):
                    check_reader(db)
        finally:
            with psycopg.connect(self.owner_url) as db:
                db.execute(sql.SQL("REVOKE UPDATE(name) ON atlas.thing FROM {}").format(sql.Identifier(self.reader)))
        with psycopg.connect(self.owner_url) as db:
            db.execute("CREATE FUNCTION public.privileged_fixture() RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'")
        try:
            with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
                with self.assertRaises(RuntimeError):
                    check_reader(db)
        finally:
            with psycopg.connect(self.owner_url) as db:
                db.execute("DROP FUNCTION public.privileged_fixture()")

    def test_queries_and_errors_and_recovery(self):
        result = self.post("WITH x AS (SELECT t.id, t.name FROM thing t JOIN link l ON l.target=t.id) SELECT name, count(*) AS n FROM x GROUP BY name")
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["rows"], [["Alpha", 1]])
        self.assertFalse(result.json()["truncated"])
        self.assertEqual(self.post("SELECT 1 AS n, 2 AS n").json()["rows"], [[1, 2]])
        for statement, code in [("SELECT missing FROM thing", "42703"), ("SELECT 1 / 0", "22012")]:
            result = self.post(statement)
            self.assertEqual(result.status_code, 400, result.text)
            self.assertEqual(result.json()["error"]["sqlstate"], code)
        result = self.post("SELEC name FROM thing")
        self.assertEqual(result.json()["error"]["code"], "syntax_error")
        self.assertIsNotNone(result.json()["error"]["position"])
        self.assertIn('"end"', result.json()["error"]["hint"])
        for statement in ["WITH x AS (DELETE FROM thing RETURNING *) SELECT * FROM x", "SELECT (123::bigint).pg_advisory_lock", "WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles"]:
            self.assertEqual(self.post(statement).status_code, 400)
        self.assertEqual(self.post("SELECT count(*) FROM thing").json()["rows"], [[1]])
        result = self.post("SELECT t.id, u.value FROM thing t CROSS JOIN LATERAL unnest(t.aliases) WITH ORDINALITY AS u(value, position)")
        self.assertEqual(result.json()["rows"], [["one", "First"]], result.text)
        result = self.post("SELECT u.value, u.position FROM unnest(ARRAY['a','b']) WITH ORDINALITY u(value, position)")
        self.assertEqual(result.json()["rows"], [["a", 1], ["b", 2]], result.text)
        result = self.post("SELECT u.* FROM unnest(ARRAY['a','b']) WITH ORDINALITY u")
        self.assertEqual(result.json()["rows"], [["a", 1], ["b", 2]], result.text)
        self.assertEqual(self.post("SELECT u.current_setting FROM unnest(ARRAY['search_path']) WITH ORDINALITY u").status_code, 400)
        result = self.client.post("/api/query", content=json.dumps({"sql": "SELECT '\ud800'"}), headers={"Content-Type": "application/json"})
        self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.post("SELECT 1\x00").status_code, 400)

    def test_startup_detects_schema_ownership_and_sequence_writes(self):
        with psycopg.connect(self.owner_url) as db:
            db.execute(sql.SQL("CREATE SCHEMA owned_fixture AUTHORIZATION {}").format(sql.Identifier(self.reader)))
            db.execute(sql.SQL("REVOKE CREATE ON SCHEMA owned_fixture FROM {}").format(sql.Identifier(self.reader)))
        try:
            with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
                with self.assertRaises(RuntimeError):
                    check_reader(db)
        finally:
            with psycopg.connect(self.owner_url) as db:
                db.execute("DROP SCHEMA owned_fixture")
        with psycopg.connect(self.owner_url) as db:
            db.execute("CREATE SEQUENCE public.sequence_fixture")
            db.execute(sql.SQL("GRANT USAGE ON SEQUENCE public.sequence_fixture TO {}").format(sql.Identifier(self.reader)))
        try:
            with psycopg.connect(self.reader_url, row_factory=dict_row) as db:
                with self.assertRaises(RuntimeError):
                    check_reader(db)
        finally:
            with psycopg.connect(self.owner_url) as db:
                db.execute("DROP SEQUENCE public.sequence_fixture")

    def test_response_bounds(self):
        result = self.post("SELECT 1 UNION ALL SELECT 2", limit=1).json()
        self.assertTrue(result["truncated"])
        self.assertEqual(result["truncation_reason"], "rows")
        self.assertEqual(result["row_count"], 1)
        self.assertFalse(self.post("SELECT 1", limit=1).json()["truncated"])
        self.assertEqual(self.post("SELECT * FROM thing WHERE false").json()["rows"], [])
        with patch.object(query, "MAX_BYTES", 1000):
            result = self.post("SELECT string_agg(name,'') FROM thing t CROSS JOIN thing u", limit=1)
            self.assertEqual(result.status_code, 400)
            result = self.post("SELECT string_agg(t.name,'') FROM thing t CROSS JOIN thing u")
            self.assertEqual(result.status_code, 200, result.text)
            result = self.post("SELECT concat('" + ("x" * 1200) + "')")
            self.assertEqual(result.status_code, 422, result.text)
            result = self.post("SELECT '" + ("x" * 300) + "' FROM thing UNION ALL SELECT '" + ("x" * 300) + "'")
            self.assertTrue(result.json()["truncated"], result.text)
            self.assertEqual(result.json()["truncation_reason"], "bytes")
        self.assertEqual(self.post("SELECT 'NaN'::float8").status_code, 422)
        self.assertEqual(self.post("SELECT 'Infinity'::float8").status_code, 422)
        self.assertEqual(self.post("SELECT 1", limit=1001).status_code, 422)

    def test_timeout_and_next_request(self):
        with patch.object(query, "TIMEOUT_MS", 100):
            result = self.post("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n")
        self.assertEqual(result.status_code, 408, result.text)
        self.assertEqual(result.json()["error"]["code"], "query_timeout")
        self.assertEqual(self.post("SELECT 1").status_code, 200)

    def test_trace_records_body_and_complete_error_response(self):
        result = self.post("SELECT nonexistent FROM thing")
        entries = [json.loads(line) for line in (self.path / "traces" / "requests.jsonl").read_text().splitlines()]
        entry = next(row for row in entries if row["request_id"] == result.json()["request_id"])
        self.assertEqual(entry["body"], {"sql": "SELECT nonexistent FROM thing"})
        self.assertEqual(entry["method"], "POST")
        self.assertEqual(entry["status"], 400)
        self.assertEqual((self.path / "traces" / entry["response_file"]).read_bytes(), result.content)
        self.assertEqual(entry["response_bytes"], len(result.content))


if __name__ == "__main__":
    unittest.main()
