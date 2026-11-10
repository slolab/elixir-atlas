# /// script
# requires-python = ">=3.12"
# dependencies = ["harbor==0.25.0", "python-dotenv", "pyyaml"]
# ///

import argparse
import asyncio
import json
import os
import shutil
from pathlib import Path

import yaml
from dotenv import load_dotenv
from harbor.job import Job
from harbor.models.job.config import JobConfig
from harbor.models.task.config import TaskConfig
from judge import ESCALATION, SCORES, judge_trial, render

CODE = Path(__file__).resolve().parent
REPO = CODE.parents[1]
TASKS, RESULTS = REPO / "eval" / "tasks", REPO / "eval" / "results"
MODEL = "openrouter/openai/gpt-6-luna"
REASONING_EFFORT = "high"
TIMEOUT_SEC = 3600
MEMORY_MB = 16384
CONCURRENCY = 4
ALLOWED_HOSTS = ["openrouter.ai", "pypi.org", "files.pythonhosted.org"]


def raw_evidence():
    volumes = [
        {"type": "bind", "source": str(REPO / "data" / "input"), "target": "/workspace/data/input", "read_only": True},
        {"type": "bind", "source": str(REPO / "data-sources-scraping.jsonl"),
         "target": "/workspace/data-sources-scraping.jsonl", "read_only": True},
        {"type": "tmpfs", "target": "/workspace/data/input/perun"},
    ]
    return {"volumes": volumes}, render("raw.md")


EVIDENCE = {"raw": raw_evidence}


def load_set(folder):
    cq_set = yaml.safe_load((folder / "set.yaml").read_text())
    cq_set["questions"] = [yaml.safe_load(path.read_text()) for path in sorted((folder / "questions").glob("*.yaml"))]
    return cq_set


def write_tasks(cq_set, evidence, root):
    shutil.rmtree(root, ignore_errors=True)
    service, prompt = EVIDENCE[evidence]()
    compose = yaml.safe_dump({"services": {"main": {"init": True, "cap_drop": ["NET_RAW"], **service}}})
    config = TaskConfig.model_validate({
        "metadata": {"cqs": cq_set["id"], "version": cq_set["version"], "evidence": evidence},
        "artifacts": ["/workspace/answer.md"],
        "environment": {"workdir": "/workspace", "memory_mb": MEMORY_MB},
        "agent": {"network_mode": "allowlist", "allowed_hosts": ALLOWED_HOSTS},
    }).model_dump_toml()
    for question in cq_set["questions"]:
        task = root / question["id"]
        (task / "environment").mkdir(parents=True)
        shutil.copy(CODE / "environment" / "Dockerfile", task / "environment" / "Dockerfile")
        (task / "environment" / "docker-compose.yaml").write_text(compose)
        (task / "task.toml").write_text(config)
        (task / "instruction.md").write_text(render(
            "qa.md", question=question["question"].strip(), context=cq_set["context"].strip(), evidence=prompt))


async def run_job(tasks, name, questions, repeats):
    job = await Job.create(JobConfig.model_validate({
        "job_name": name, "jobs_dir": str(RESULTS), "n_attempts": repeats, "n_concurrent_trials": CONCURRENCY,
        "datasets": [{"path": str(tasks), "task_names": questions}],
        "agents": [{"name": "codex", "model_name": MODEL, "override_timeout_sec": TIMEOUT_SEC,
                    "kwargs": {"reasoning_effort": REASONING_EFFORT, "web_search": "disabled"}}],
        "environment": {"type": "docker"}, "verifier": {"disable": True},
    }))
    await job.run()


def report(job_dir, cq_set):
    questions = {question["id"]: question for question in cq_set["questions"]}
    rows, judge_cost, agent_cost = [], 0, 0
    for trial in sorted(path for path in job_dir.iterdir() if (path / "result.json").is_file()):
        result = json.loads((trial / "result.json").read_text())
        judgement = judge_trial(trial, questions[result["task_name"]], cq_set)
        error = (result.get("exception_info") or {}).get("exception_type", "")
        rows.append((result["task_name"], judgement["grades"], error))
        judge_cost += judgement["cost_usd"]
        agent_cost += (result.get("agent_result") or {}).get("cost_usd") or 0
    rubrics = [rubric["name"] for rubric in cq_set["rubric"]]
    print("\n" + "  ".join(["question".ljust(20), *(name.ljust(22) for name in rubrics), "agent error"]))
    for question, grades, error in sorted(rows):
        cells = [grades[name]["verdict"] + (" (escalated)" if grades[name]["judge"] == ESCALATION else "")
                 for name in rubrics]
        print("  ".join([question.ljust(20), *(cell.ljust(22) for cell in cells), error]))
    for name in rubrics:
        mean = sum(SCORES[grades[name]["verdict"]] for _, grades, _ in rows) / len(rows)
        print(f"{name}: mean score {mean:.2f} over {len(rows)} answers")
    print(f"cost: agent ${agent_cost:.4f}, judge ${judge_cost:.4f}\nresults: {job_dir}")


def main():
    parser = argparse.ArgumentParser(description="Answer a CQ set's questions with an agent on Harbor and judge them.")
    parser.add_argument("set", type=Path, help="a CQ set folder, such as eval/cqs/atlas_261110")
    parser.add_argument("--evidence", choices=EVIDENCE, default="raw")
    parser.add_argument("--questions", nargs="+", metavar="ID", help="question numbers or IDs; all by default")
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    load_dotenv(REPO / ".env")
    os.environ["HARBOR_TELEMETRY"] = "off"
    cq_set = load_set(args.set.resolve())
    questions = [q if q.startswith(cq_set["id"]) else f"{cq_set['id']}-{q}" for q in args.questions or []] or None
    tasks = f"{cq_set['id']}-v{cq_set['version']}__{args.evidence}"
    selection = [q.rsplit("-", 1)[1] for q in questions or []] + ([f"x{args.repeats}"] if args.repeats > 1 else [])
    name = "__".join([tasks, MODEL.rsplit("/", 1)[1], *(["-".join(selection)] if selection else [])])
    write_tasks(cq_set, args.evidence, TASKS / tasks)
    asyncio.run(run_job(TASKS / tasks, name, questions, args.repeats))
    report(RESULTS / name, cq_set)


if __name__ == "__main__":
    main()
