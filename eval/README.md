# Evaluation

`user_stories.md` holds the end-to-end use cases (A, B, C) that the CQ sets are built from. The scripts that run and annotate the evaluation are in `src/eval/`. `cqs/<set-id>/` holds a competency-question (CQ) set, a simplified version of the biotope-bench layout:

- `set.yaml`: the set's `id`, its `version`, the users' `purpose`, the data snapshot it was written against (`reference_dataset`), the `context` that answering agents see and the `correctness` `rubric`.
- `questions/<set-id>-NNN.yaml`: one question with its `use_case` (a question id from `user_stories.md`, such as `B4`), `question`, `answerability`, `reference_answer`, `eval_notes` (the components the rubric scores) and `sources` (paths under `data/`).
- `sidenotes.md`: how the answers were derived, data-quality notes and details left out of the answers.

Retired sets are in `archive/`.

The rubric measures accuracy: whether the answer's facts are correct. Argilla collects how users like the answers: annotators see each question with its reference answer, rate it from 1 to 5 and can leave feedback.

## Run the evaluation

```bash
uv run src/eval/run.py eval/cqs/atlas_261111
uv run src/eval/run.py eval/cqs/atlas_261111 --questions 006 007 --repeats 3
```

`run.py` turns each question into a [Harbor](https://github.com/laude-institute/harbor) task in `eval/tasks/`, and Harbor runs Codex with `openai/gpt-6-luna` at reasoning effort high in Docker. The shared image preinstalls Codex 0.167.1 so trials reuse the cached installation instead of downloading Node.js and Codex for each question. With `--evidence raw`, the default, the agent reads all of `data/input` read-only and the URL index `data-sources-scraping.jsonl`; it can reach only OpenRouter and PyPI. It writes its answer to `answer.md`.

`judge.py` then grades every answer by the set's rubrics with `openai/gpt-6-luna-decisions` on OpenRouter's decisions API. A verdict with a confidence below 0.8 is graded again by `openai/gpt-6.1-sol` at reasoning effort high. Each trial in `eval/results/<job>/` keeps its `judgement.json`, and the script prints a score table. Each choice of `--questions` and `--repeats` is its own job, such as `atlas_261111-v1__raw__gpt-6-luna__006-007-x3`. Rerunning the same command resumes unfinished trials and grades again only answers whose inputs changed.

Use `--api-url` to evaluate another Atlas deployment. The copied API reference and network allowlist use that address; the distributed skill stays unchanged. A local service must be reachable from Docker, not just the host's loopback address. Use PostgreSQL when comparing with Railway: the SQLite backend has different search semantics and ranking.

`judge.py` then grades every answer by the set's rubrics with `openai/gpt-6-luna-decisions` on OpenRouter's decisions API. A verdict with a confidence below 0.8 is graded again by `openai/gpt-6.1-sol` at reasoning effort high. Each trial in `eval/results/<job>/` keeps its `judgement.json`, and the script prints a score table. Each choice of `--questions` and `--repeats` is its own job, such as `atlas_261110-v1__raw__baseline__gpt-6-luna__006-007-x3`. Rerunning the same command resumes unfinished trials and grades again only answers whose inputs changed.

Use a new `--experiment` name after changing the skill, runner, prompts, CQ set, API or data. Task instructions and the skill are copied once and guarded by `experiment.json`; changed recorded inputs cannot replace an existing experiment. The manifest records file hashes and the API release or raw snapshot identity. SQL-capable deployments include an API code fingerprint in the release metadata. API code changes require a new experiment name even if the data release is unchanged. Keep the API and raw files stable during a run. `--prepare-only` generates tasks without running agents or judges.

Evidence modes are entries of `EVIDENCE` in `run.py`. Each returns the agent's mounts or services, evidence prompt and network allowlist.

The script needs `OPENROUTER_API_KEY` in `.env` and Docker. Only raw mode needs the pulled data snapshot.

## Traces

Harbor retains each trial's `agent/trajectory.json`, native Codex sessions under `agent/sessions/`, execution logs, configuration, timing, token usage and errors. `artifacts/workspace/answer.md` holds the answer; API mode also collects `artifacts/workspace/evidence/`. The agent archive includes HTTP methods and full POST bodies, including SQL. Check its request log against tool calls before assuming it is complete. For a local API started with `ATLAS_TRACE_DIR`, pass `--api-traces /path/to/traces`: the runner independently archives server-recorded requests and complete responses under the job’s `api-traces/`, including failed queries. Request IDs correlate SQL responses with those records. The directory is never mounted into agent containers. `traces.json` links to each trial’s results, grades, trajectory and evidence archive. Unknown costs remain unknown.

Read failed trials and a few expensive successes. Use tool arguments, returned evidence and saved responses to explain behavior; the final answer alone cannot distinguish a missed search from a missing fact. A trace records observable execution, not a guarantee of access to every internal reasoning step.

## Iteration principles

These are working guidelines, not an automated optimization loop:

1. Freeze a baseline with the current CQ set, data release, model and budgets. Keep raw and skill/API results separate. Review failures against the reference answers when data or CQ versions differ.
2. Diagnose the first failure: correct evidence available but missed suggests a skill problem; existing graph facts difficult to retrieve suggest an API problem; missing or incorrect extracted facts or relationships suggest a build/topology problem. Also check source coverage, infrastructure errors and grader mistakes.
3. Make focused skill or API changes and rerun affected questions, plus a small regression sample. Keep the other layers fixed where possible. Repeat promising comparisons before treating a single changed result as an improvement.
4. Batch confirmed build issues with source examples, affected CQs and expected corrections. Validate those corrections, rebuild a release, then rerun the full benchmark before publication. Reuse a raw baseline only while its data, questions, model and budgets still match.
5. Keep some new questions out of tuning. The current CQs become regression tests once their traces guide changes. Track correctness and evidence support first; use runtime, tokens, repeated searches and API errors to diagnose cost and friction.

This follows the trace-based evaluation guidance from [OpenAI](https://developers.openai.com/blog/eval-skills) and [Anthropic](https://www.anthropic.com/research/demystifying-evals-for-ai-agents), including [tool-level diagnostics and held-out tests](https://www.anthropic.com/research/writing-tools-for-agents).

## Push to Argilla

```bash
uv run src/eval/push_argilla.py eval/cqs/atlas_261111
```

The script needs `ARGILLA_API_KEY` (an owner key) in `.env`. It writes to the `elixir-atlas` workspace on `https://test.senantix.com`, in a dataset named `<set-id>-v<version>`, and creates both if needed. Rerunning it updates that dataset from the YAMLs: changed questions are updated, new ones are added and deleted ones are removed.

Once annotators have started, do not edit a version in place. Raise `version` in `set.yaml` and rerun; the new questions go to a new dataset, and the old dataset keeps its responses.

## Local SQL comparison

Start the [local PostgreSQL API](../server/README.md#local-postgresql-api), then run:

```bash
uv run src/eval/run.py eval/cqs/atlas_261110 --evidence skill-api \
  --experiment sql-local --api-url http://host.docker.internal:8811 \
  --api-probe-url http://127.0.0.1:8811 \
  --api-traces /tmp/atlas-sql-api-traces
```

Docker Desktop resolves `host.docker.internal` to the host. `--api-probe-url` lets the host runner inspect the same API through loopback; agents still receive the container-reachable URL. This experiment mounts only the skill into answering containers. PostgreSQL, its files, credentials, and server traces stay outside them. Keep the API stable during the run. Compare correctness, request counts, response bytes, SQL errors/retries and runtime with the frozen HTTP baseline; changes in CQ context or model settings invalidate a controlled quality comparison.

The first local SQL run on 11 November 2026 used the exact CQ snapshot and data release from `api-cached-20261111`, with the same model and reasoning settings. All ten trials completed. Requests fell from 299 to 129 and response bodies from 5.61 MB to 3.28 MB, while the graded mean fell from 0.55 to 0.40. This is an efficiency gain and an observed quality regression in one run; API and skill changes were evaluated together. The three downgraded answers lost a co-lead qualifier, missed source conflicts, or left a numbered deliverable match unresolved. These need evidence-level review before further tuning.

Local artifacts are in `results/atlas_261110-v1__skill-api__sql-local-20261111-v1__gpt-6-luna/`: `comparison.json`, `trace-audit.json`, `cq-set.json`, native agent traces, answers, grades, agent response archives, and independent server traces. The audit verified all 129 responses and matched all 49 SQL request bodies and responses to server request IDs. No SQL result was truncated. Railway was not updated. A separate one-query activity diagnostic is in `results/sql-activity-local-20261111/`; its interpretation is no linked dated activity in the snapshot, not proof of public inactivity.
