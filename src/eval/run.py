# /// script
# requires-python = ">=3.12"
# dependencies = ["harbor==0.25.0", "python-dotenv", "pyyaml"]
# ///

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
import urllib.request
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
API_URL = "https://atlas-production-d392fb6d.up.railway.app"
SKILL = REPO / "skills" / "agentic-elixir"


def raw_evidence(api_url):
    volumes = [
        {"type": "bind", "source": str(REPO / "data" / "input"), "target": "/workspace/data/input", "read_only": True},
        {"type": "bind", "source": str(REPO / "data-sources-scraping.jsonl"),
         "target": "/workspace/data-sources-scraping.jsonl", "read_only": True},
    ]
    return {"volumes": volumes}, render("raw.md"), ALLOWED_HOSTS


def skill_api_evidence(api_url):
    return {}, render("skill_api.md", api_url=api_url), [*ALLOWED_HOSTS, urllib.parse.urlsplit(api_url).hostname]


EVIDENCE = {"raw": raw_evidence, "skill-api": skill_api_evidence}


def load_set(folder):
    cq_set = yaml.safe_load((folder / "set.yaml").read_text())
    cq_set["questions"] = [yaml.safe_load(path.read_text()) for path in sorted((folder / "questions").glob("*.yaml"))]
    return cq_set


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def experiment_inputs(cq_set, evidence, api_url, probe_url=None):
    files = [Path(__file__), CODE / "environment" / "Dockerfile", CODE / "prompts" / "qa.md",
             CODE / "prompts" / ("skill_api.md" if evidence == "skill-api" else "raw.md")]
    inputs = {"cq_sha256": digest(cq_set), "evidence": evidence}
    if evidence == "skill-api":
        files.extend(sorted(path for path in SKILL.rglob("*") if path.is_file()))
        with urllib.request.urlopen((probe_url or api_url) + "/api/release", timeout=30) as response:
            inputs["api_release"] = json.load(response)
        inputs["api_url"] = api_url
    elif (REPO / "data" / ".snapshot.json").is_file():
        inputs["raw_snapshot"] = json.loads((REPO / "data" / ".snapshot.json").read_text())["id"]
    inputs["files_sha256"] = {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    return inputs


def write_tasks(cq_set, evidence, root, api_url=API_URL, inputs=None):
    manifest = root / "experiment.json"
    if manifest.is_file():
        if json.loads(manifest.read_text()) != inputs:
            raise ValueError("Experiment inputs changed. Use a new --experiment name to keep earlier trials and traces.")
        return
    if root.exists():
        raise ValueError("Task directory already exists without an experiment manifest. Use a new --experiment name.")
    service, prompt, hosts = EVIDENCE[evidence](api_url)
    compose = yaml.safe_dump({"services": {"main": {"init": True, "cap_drop": ["NET_RAW"], **service}}})
    config = TaskConfig.model_validate({
        "metadata": {"cqs": cq_set["id"], "version": cq_set["version"], "evidence": evidence},
        "artifacts": ["/workspace/answer.md", *(["/workspace/evidence"] if evidence == "skill-api" else [])],
        "environment": {"workdir": "/workspace", "memory_mb": MEMORY_MB},
        "agent": {"network_mode": "allowlist", "allowed_hosts": hosts},
    }).model_dump_toml()
    for question in cq_set["questions"]:
        task = root / question["id"]
        (task / "environment").mkdir(parents=True)
        shutil.copy(CODE / "environment" / "Dockerfile", task / "environment" / "Dockerfile")
        if evidence == "skill-api":
            target = task / "environment" / "skill"
            shutil.copytree(SKILL, target)
            reference = target / "references" / "api.md"
            reference.write_text(reference.read_text().replace(API_URL, api_url))
            with (task / "environment" / "Dockerfile").open("a") as dockerfile:
                dockerfile.write("\nCOPY skill /workspace/.agents/skills/agentic-elixir\nRUN mkdir -p /workspace/evidence\n")
        (task / "environment" / "docker-compose.yaml").write_text(compose)
        (task / "task.toml").write_text(config)
        (task / "instruction.md").write_text(render(
            "qa.md", question=question["question"].strip(), context=cq_set["context"].strip(), evidence=prompt))
    manifest.write_text(json.dumps(inputs, indent=2) + "\n")


async def run_job(tasks, name, questions, repeats):
    job = await Job.create(JobConfig.model_validate({
        "job_name": name, "jobs_dir": str(RESULTS), "n_attempts": repeats, "n_concurrent_trials": CONCURRENCY,
        "datasets": [{"path": str(tasks), "task_names": questions}],
        "agents": [{"name": "codex", "model_name": MODEL, "override_timeout_sec": TIMEOUT_SEC,
                    "kwargs": {"reasoning_effort": REASONING_EFFORT, "web_search": "disabled"}}],
        "environment": {"type": "docker"}, "verifier": {"disable": True},
    }))
    shutil.copy(tasks / "experiment.json", job.job_dir / "experiment.json")
    await job.run()


def report(job_dir, cq_set):
    questions = {question["id"]: question for question in cq_set["questions"]}
    rows, traces, judge_cost, agent_cost, unknown_costs = [], [], 0, 0, 0
    for trial in sorted(path for path in job_dir.iterdir() if (path / "result.json").is_file()):
        result = json.loads((trial / "result.json").read_text())
        judgement = judge_trial(trial, questions[result["task_name"]], cq_set)
        error = (result.get("exception_info") or {}).get("exception_type", "")
        rows.append((result["task_name"], judgement["grades"], error))
        judge_cost += judgement["cost_usd"]
        cost = (result.get("agent_result") or {}).get("cost_usd")
        unknown_costs += cost is None
        agent_cost += cost or 0
        trajectory = trial / "agent" / "trajectory.json"
        traces.append({"question": result["task_name"], "trial": trial.name,
                       "trajectory": str(trajectory.relative_to(job_dir)) if trajectory.is_file() else None,
                       "answer": str((trial / "artifacts" / "workspace" / "answer.md").relative_to(job_dir)),
                       "evidence": str((trial / "artifacts" / "workspace" / "evidence").relative_to(job_dir))
                       if (trial / "artifacts" / "workspace" / "evidence").is_dir() else None,
                       "result": str((trial / "result.json").relative_to(job_dir)),
                       "judgement": str((trial / "judgement.json").relative_to(job_dir))})
    (job_dir / "traces.json").write_text(json.dumps(traces, indent=2) + "\n")
    rubrics = [rubric["name"] for rubric in cq_set["rubric"]]
    print("\n" + "  ".join(["question".ljust(20), *(name.ljust(22) for name in rubrics), "agent error"]))
    for question, grades, error in sorted(rows):
        cells = [grades[name]["verdict"] + (" (escalated)" if grades[name]["judge"] == ESCALATION else "")
                 for name in rubrics]
        print("  ".join([question.ljust(20), *(cell.ljust(22) for cell in cells), error]))
    for name in rubrics if rows else []:
        mean = sum(SCORES[grades[name]["verdict"]] for _, grades, _ in rows) / len(rows)
        print(f"{name}: mean score {mean:.2f} over {len(rows)} answers")
    missing = sum(trace["trajectory"] is None for trace in traces)
    print(f"cost: recorded agent ${agent_cost:.4f} ({unknown_costs} unknown), judge ${judge_cost:.4f}")
    print(f"traces: {len(traces) - missing}/{len(traces)} trajectories\nresults: {job_dir}")


def main():
    parser = argparse.ArgumentParser(description="Answer a CQ set's questions with an agent on Harbor and judge them.")
    parser.add_argument("set", type=Path, help="a CQ set folder, such as eval/cqs/atlas_261110")
    parser.add_argument("--evidence", choices=EVIDENCE, default="raw")
    parser.add_argument("--questions", nargs="+", metavar="ID", help="question numbers or IDs; all by default")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--experiment", default="baseline", help="name for this fixed set of experiment inputs")
    parser.add_argument("--api-url", default=API_URL, help="Atlas API base URL for skill-api mode")
    parser.add_argument("--api-probe-url", help="host-side URL for release inspection when the container URL is not resolvable on the host")
    parser.add_argument("--prepare-only", action="store_true", help="generate isolated tasks without running agents or judges")
    parser.add_argument("--api-traces", type=Path, help="local API trace directory to archive after the run; never mounted into agent containers")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.experiment):
        parser.error("--experiment must contain only letters, numbers, underscores or hyphens")
    args.api_url = args.api_url.rstrip("/")
    url = urllib.parse.urlsplit(args.api_url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("--api-url must be an HTTP(S) base URL without credentials, query or fragment")
    load_dotenv(REPO / ".env")
    os.environ["HARBOR_TELEMETRY"] = "off"
    cq_set = load_set(args.set.resolve())
    questions = [q if q.startswith(cq_set["id"]) else f"{cq_set['id']}-{q}" for q in args.questions or []] or None
    tasks = f"{cq_set['id']}-v{cq_set['version']}__{args.evidence}__{args.experiment}"
    selection = [q.rsplit("-", 1)[1] for q in questions or []] + ([f"x{args.repeats}"] if args.repeats > 1 else [])
    name = "__".join([tasks, MODEL.rsplit("/", 1)[1], *(["-".join(selection)] if selection else [])])
    inputs = experiment_inputs(cq_set, args.evidence, args.api_url, args.api_probe_url)
    write_tasks(cq_set, args.evidence, TASKS / tasks, args.api_url, inputs)
    if args.prepare_only:
        print(TASKS / tasks)
        return
    started = time.time()
    try:
        asyncio.run(run_job(TASKS / tasks, name, questions, args.repeats))
    finally:
        if args.api_traces and (RESULTS / name).is_dir():
            archive_api_traces(args.api_traces, RESULTS / name / "api-traces", started)
    report(RESULTS / name, cq_set)


def archive_api_traces(source, target, started):
    from datetime import datetime
    source = source.resolve()
    if not (source / "requests.jsonl").is_file():
        print(f"No server trace log found at {source}; agent traces remain in the job directory.")
        return
    target.mkdir(exist_ok=True)
    with (source / "requests.jsonl").open() as entries, (target / "requests.jsonl").open("a") as stream:
        for line in entries:
            entry = json.loads(line)
            if datetime.fromisoformat(entry["time"]).timestamp() < started:
                continue
            filename = entry["response_file"]
            if Path(filename).name != filename:
                raise ValueError("API trace response must be a filename")
            shutil.copy(source / filename, target / filename)
            stream.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    main()
