import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from atlas_api import views
from atlas_api.main import app
from atlas_api.sqlite_snapshot import Snapshot


def topic_fixture(path):
    tables = {
        "Topic": "id TEXT PRIMARY KEY,label TEXT",
        "Initiative": "id TEXT PRIMARY KEY,name TEXT,kind TEXT,contacts TEXT,join_url TEXT,joining TEXT,pages TEXT",
        "InitiativeTopic": "id TEXT PRIMARY KEY,source TEXT,target TEXT,evidence TEXT,source_url TEXT,retrieved_at TEXT",
        "ToolTopic": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "MaterialTopic": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "EventTopic": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "ToolFor": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "Person": "id TEXT PRIMARY KEY,name TEXT",
        "HoldsRole": "id TEXT PRIMARY KEY,source TEXT,target TEXT,role_kind TEXT",
        "Resource": "id TEXT PRIMARY KEY,name TEXT,kind TEXT,url TEXT",
        "Recommends": "id TEXT PRIMARY KEY,source TEXT,target TEXT,basis TEXT,purpose TEXT,evidence TEXT,source_url TEXT",
        "IsTool": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "Tool": "id TEXT PRIMARY KEY,name TEXT,homepage TEXT,url TEXT,tool_types TEXT",
        "OutputOf": "id TEXT PRIMARY KEY,source TEXT,target TEXT",
        "Output": "id TEXT PRIMARY KEY,title TEXT,date TEXT,url TEXT,doi TEXT,kind TEXT,resource_type TEXT",
        "TrainingMaterial": "id TEXT PRIMARY KEY,title TEXT,url TEXT,date_published TEXT,content_provider TEXT",
        "Event": 'id TEXT PRIMARY KEY,title TEXT,url TEXT,start TEXT,"end" TEXT,city TEXT,country TEXT,online INTEGER',
    }
    records = {
        "Topic": [("systems", "Systems biology"), ("metabolic", "Metabolic engineering"), ("empty", "Unlinked area")],
        "Initiative": [
            ("community:systems", "Systems Biology", "community", '["contact@example.org"]', "https://example.org/join", None, '["https://example.org/community"]'),
            ("community:tools", "Tool-linked Community", "community", "[]", None, None, "[]"),
            ("project:systems", "Research project", "eu_project", "[]", None, None, "[]"),
        ],
        "InitiativeTopic": [
            ("it1", "community:systems", "systems", "We study systems.", "https://example.org/community", "2026-11-11"),
            ("it2", "community:systems", "systems", "A second statement.", "https://example.org/other", "2026-11-10"),
            ("it3", "community:systems", "metabolic", "Metabolic models.", "https://example.org/community", "2026-11-11"),
            ("it4", "project:systems", "systems", "A project.", None, None),
        ],
        "Tool": [
            ("tool:recommended", "Recommended tool", "https://example.org/recommended", "https://bio.tools/recommended", '["Analysis"]'),
            ("tool:listed", "Catalogue tool", "https://example.org/listed", "https://bio.tools/listed", "[]"),
        ],
        "ToolTopic": [("tt1", "tool:recommended", "systems"), ("tt2", "tool:listed", "systems"), ("tt3", "tool:listed", "metabolic")],
        "ToolFor": [("tf1", "tool:listed", "community:tools")],
        "Person": [("person:lead", "Community lead")],
        "HoldsRole": [("h1", "person:lead", "community:systems", "co_lead"), ("h2", "person:lead", "community:systems", "contact")],
        "Resource": [("resource:tool", "Recommended tool", "tool", None), ("resource:standard", "Community standard", "standard", "https://example.org/standard")],
        "Recommends": [
            ("r1", "community:systems", "resource:tool", "recommends", "Build a model", "We recommend this tool.", "https://example.org/paper"),
            ("r2", "community:systems", "resource:standard", "develops", "Exchange models", "We developed this standard.", "https://example.org/standard"),
        ],
        "IsTool": [("is1", "resource:tool", "tool:recommended")],
        "Output": [("paper:1", "Community white paper", "2026-01", "https://example.org/paper", None, "article", None)],
        "OutputOf": [("of1", "paper:1", "community:systems"), ("of2", "paper:1", "community:systems")],
        "TrainingMaterial": [("material:1", "Modelling tutorial", "https://example.org/tutorial", "2026-02", "Training provider")],
        "MaterialTopic": [("mt1", "material:1", "systems"), ("mt2", "material:1", "metabolic")],
        "Event": [
            ("event:past", "Past workshop", "https://example.org/past", "2025-01-01", None, None, None, 1),
            ("event:today", "Today's workshop", "https://example.org/today", "2026-11-12", None, None, None, 1),
            ("event:future", "Future workshop", "https://example.org/future", "2027-01-01", None, None, None, 1),
        ],
        "EventTopic": [("et1", "event:past", "systems"), ("et2", "event:today", "systems"), ("et3", "event:future", "metabolic")],
    }
    with closing(sqlite3.connect(path)) as db, db:
        for name, columns in tables.items():
            db.execute(f'CREATE TABLE "{name}" ({columns})')
        for name, entries in records.items():
            placeholders = ",".join("?" for _ in entries[0])
            db.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})', entries)


class TopicTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "graph.sqlite"
        topic_fixture(self.path)

    def test_cross_referencing_preserves_evidence_and_distinctions(self):
        with closing(Snapshot(self.path)) as db:
            topics = {row["id"]: row for row in views.topics(db)}
            self.assertEqual(topics["systems"]["communities"], 2)
            result = views.topic_support(db, ["systems", "metabolic"], "2026-11-12")
            self.assertEqual([c["id"] for c in result["communities"]], ["community:systems", "community:tools"])
            community = result["communities"][0]
            self.assertEqual(len(community["topics"]), 2)
            self.assertEqual(community["contacts"], ["contact@example.org"])
            self.assertEqual(len(community["leads"]), 1)
            self.assertTrue(community["topics"][0]["source_url"])
            self.assertEqual({b["basis"] for r in result["resources"] for b in r["by"]}, {"recommends", "develops"})
            self.assertEqual([t["id"] for t in result["tools"]], ["tool:listed"])
            self.assertEqual(result["tools"][0]["listed_for"], "Tool-linked Community")
            self.assertEqual(result["papers_total"], 1)
            self.assertEqual(result["materials_total"], 1)
            self.assertEqual([e["id"] for e in result["events"]], ["event:today", "event:future"])
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("DELETE FROM Topic")

    def test_empty_area_has_a_complete_response(self):
        with closing(Snapshot(self.path)) as db:
            result = views.topic_support(db, ["empty"], "2026-11-12")
            for key in ("communities", "resources", "tools", "papers", "materials", "events"):
                self.assertEqual(result[key], [])
            for key in ("tools_total", "papers_total", "materials_total", "events_total"):
                self.assertEqual(result[key], 0)

    def test_adding_an_or_topic_keeps_tool_linked_community_recommendations(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM InitiativeTopic WHERE source='community:systems' AND target='metabolic'")
            db.execute("INSERT INTO Resource VALUES (?,?,?,?)", ("resource:tool-only", "Tool-linked recommendation", "standard", "https://example.org/tool-only"))
            db.execute("INSERT INTO Recommends VALUES (?,?,?,?,?,?,?)", ("r3", "community:tools", "resource:tool-only", "recommends", "Build models", "Our recommendation.", "https://example.org/tool-community"))
            db.execute("INSERT INTO Recommends VALUES (?,?,?,?,?,?,?)", ("r4", "community:tools", "resource:standard", "recommends", "Exchange models", "We recommend this standard.", "https://example.org/tool-community"))
        with closing(Snapshot(self.path)) as db:
            before = views.topic_support(db, ["metabolic"], "2026-11-12")
            after = views.topic_support(db, ["metabolic", "systems"], "2026-11-12")
            self.assertEqual([c["id"] for c in before["communities"]], ["community:tools"])
            self.assertEqual({c["id"] for c in after["communities"]}, {"community:tools", "community:systems"})
            before_resources = {r["id"] for r in before["resources"]}
            self.assertIn("resource:tool-only", before_resources)
            self.assertTrue(before_resources.issubset({r["id"] for r in after["resources"]}))
            standard = next(r for r in after["resources"] if r["id"] == "resource:standard")
            self.assertEqual({b["community"] for b in standard["by"]}, {"Systems Biology", "Tool-linked Community"})

    def test_unnamed_tools_use_their_id_as_a_visible_name(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            for identifier, name in (("tool:unnamed", None), ("tool:empty-name", "")):
                db.execute("INSERT INTO Tool VALUES (?,?,?,?,?)", (identifier, name, None, "https://bio.tools/example", "[]"))
                db.execute("INSERT INTO ToolTopic VALUES (?,?,?)", (identifier, identifier, "systems"))
        with closing(Snapshot(self.path)) as db:
            result = views.topic_support(db, ["systems"], "2026-11-12")
            tools = {t["id"]: t for t in result["tools"]}
            self.assertEqual(result["tools_total"], 3)
            self.assertEqual(tools["tool:unnamed"]["name"], "tool:unnamed")
            self.assertEqual(tools["tool:empty-name"]["name"], "tool:empty-name")
            self.assertEqual(tools["tool:listed"]["name"], "Catalogue tool")

    def test_material_limits_report_the_full_distinct_count(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            for number in range(45):
                identifier = f"material:extra-{number}"
                db.execute("INSERT INTO TrainingMaterial VALUES (?,?,?,?,?)", (identifier, f"Tutorial {number}", None, None, None))
                db.execute("INSERT INTO MaterialTopic VALUES (?,?,?)", (f"extra-{number}", identifier, "systems"))
        with closing(Snapshot(self.path)) as db:
            result = views.topic_support(db, ["systems", "metabolic"], "2026-11-12")
            self.assertEqual(result["materials_total"], 46)
            self.assertEqual(len(result["materials"]), 40)
            self.assertEqual(len({m["id"] for m in result["materials"]}), 40)

    def test_http_input_validation_and_read_only_routes(self):
        with patch.dict(os.environ, {"ATLAS_SQLITE_PATH": str(self.path)}), TestClient(app) as client:
            self.assertEqual(client.get("/api/topics").status_code, 200)
            result = client.get("/api/topic-support", params={"topics": " systems,systems,metabolic "})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(len(result.json()["topics"]), 2)
            for value in ("", " , ", "unknown", "systems,unknown", "systems'); DROP TABLE Topic;--", ",".join(str(n) for n in range(11))):
                self.assertEqual(client.get("/api/topic-support", params={"topics": value}).status_code, 422, value)
            self.assertEqual(client.post("/api/topic-support?topics=systems").status_code, 405)
            self.assertEqual(len(client.get("/api/topics").json()), 3)

    def test_older_snapshots_explain_how_to_upgrade(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DROP TABLE Resource")
        with patch.dict(os.environ, {"ATLAS_SQLITE_PATH": str(self.path)}), TestClient(app) as client:
            result = client.get("/api/topic-support?topics=systems")
            self.assertEqual(result.status_code, 409)
            self.assertIn("newer Atlas snapshot", result.json()["detail"])


if __name__ == "__main__":
    unittest.main()
