import json
import tempfile
import tomllib
import unittest
from pathlib import Path

import yaml

from run import ALLOWED_HOSTS, SKILL, archive_api_traces, write_tasks


class EvidenceIsolationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "tasks"
        self.cqs = {"id": "test", "version": 1, "context": "Use the supplied evidence.", "questions": [
            {"id": "test-001", "question": "Which Communities overlap?",
             "reference_answer": "PRIVATE_REFERENCE_SENTINEL", "eval_notes": "PRIVATE_GRADER_SENTINEL"}
        ]}
        self.inputs = {"revision": "one"}

    def tearDown(self):
        self.directory.cleanup()

    def test_skill_api_has_no_data_mounts_or_reference_answers(self):
        write_tasks(self.cqs, "skill-api", self.root, "https://atlas.example", self.inputs)
        task = self.root / "test-001"
        service = yaml.safe_load((task / "environment/docker-compose.yaml").read_text())["services"]["main"]
        self.assertFalse(service.get("volumes"))
        config = tomllib.loads((task / "task.toml").read_text())
        self.assertEqual(config["agent"]["network_mode"], "allowlist")
        self.assertEqual(config["agent"]["allowed_hosts"], [*ALLOWED_HOSTS, "atlas.example"])
        self.assertIn("/workspace/evidence", config["artifacts"])
        copied = task / "environment/skill"
        self.assertEqual((copied / "SKILL.md").read_bytes(), (SKILL / "SKILL.md").read_bytes())
        self.assertIn("https://atlas.example", (copied / "references/api.md").read_text())
        for path in task.rglob("*"):
            if path.is_file():
                self.assertNotIn("PRIVATE_REFERENCE_SENTINEL", path.read_text())
                self.assertNotIn("PRIVATE_GRADER_SENTINEL", path.read_text())

    def test_raw_exposes_all_input_read_only(self):
        write_tasks(self.cqs, "raw", self.root, inputs=self.inputs)
        task = self.root / "test-001"
        service = yaml.safe_load((task / "environment/docker-compose.yaml").read_text())["services"]["main"]
        mounts = {volume["target"]: volume for volume in service["volumes"]}
        self.assertEqual(set(mounts), {"/workspace/data/input", "/workspace/data-sources-scraping.jsonl"})
        self.assertTrue(all(volume["type"] == "bind" for volume in mounts.values()))
        self.assertTrue(mounts["/workspace/data/input"]["read_only"])
        self.assertTrue(mounts["/workspace/data-sources-scraping.jsonl"]["read_only"])
        config = tomllib.loads((task / "task.toml").read_text())
        self.assertEqual(config["agent"]["allowed_hosts"], ALLOWED_HOSTS)
        self.assertFalse((task / "environment/skill").exists())

    def test_changed_experiment_cannot_replace_saved_inputs(self):
        write_tasks(self.cqs, "raw", self.root, inputs=self.inputs)
        instruction = self.root / "test-001/instruction.md"
        before = instruction.read_bytes()
        write_tasks(self.cqs, "raw", self.root, inputs=self.inputs)
        with self.assertRaisesRegex(ValueError, "new --experiment"):
            write_tasks(self.cqs, "raw", self.root, inputs={"revision": "two"})
        self.assertEqual(instruction.read_bytes(), before)
        self.assertEqual(json.loads((self.root / "experiment.json").read_text()), self.inputs)

    def test_server_trace_archive_preserves_sql_and_failed_response(self):
        source = Path(self.directory.name) / "api"
        source.mkdir()
        (source / "response.json").write_text('{"error":{"sqlstate":"42703"}}')
        entry = {"time": "2026-11-11T12:00:00+00:00", "method": "POST", "body": {"sql": "SELECT missing FROM initiative"},
                 "status": 400, "response_file": "response.json"}
        (source / "requests.jsonl").write_text(json.dumps({**entry, "time": "2020-01-01T00:00:00+00:00"}) + "\n" + json.dumps(entry) + "\n")
        target = Path(self.directory.name) / "archived"
        archive_api_traces(source, target, 1700000000)
        self.assertEqual([json.loads(line) for line in (target / "requests.jsonl").read_text().splitlines()], [entry])
        self.assertEqual((target / "response.json").read_bytes(), (source / "response.json").read_bytes())

    def test_missing_server_traces_do_not_hide_run_failure(self):
        target = Path(self.directory.name) / "archived"
        with self.assertRaisesRegex(RuntimeError, "agent setup failed"):
            try:
                raise RuntimeError("agent setup failed")
            finally:
                archive_api_traces(Path(self.directory.name) / "missing", target, 0)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
