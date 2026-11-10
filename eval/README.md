# Evaluation

`user_stories.md` holds the user stories. The scripts that run and annotate the evaluation are in `src/eval/`. `cqs/<set-id>/` holds a competency-question (CQ) set, a simplified version of the biotope-bench layout:

- `set.yaml`: the set's `id`, its `version`, the users' `purpose`, the data snapshot it was written against (`reference_dataset`), the `context` that answering agents see and the `correctness` `rubric`.
- `questions/<set-id>-NNN.yaml`: one question with its `user_story`, `question`, `answerability`, `reference_answer`, `eval_notes` (the components the rubric scores) and `sources` (paths under `data/`).
- `sidenotes.md`: how the answers were derived, data-quality notes and details left out of the answers.

The rubric measures accuracy: whether the answer's facts are correct. Argilla collects how users like the answers: annotators see each question with its reference answer, rate it from 1 to 5 and can leave feedback.

## Run the evaluation

```bash
uv run src/eval/run.py eval/cqs/atlas_261110
uv run src/eval/run.py eval/cqs/atlas_261110 --questions 006 007 --repeats 3
```

`run.py` turns each question into a [Harbor](https://github.com/laude-institute/harbor) task in `eval/tasks/`, and Harbor runs Codex with `openai/gpt-6-luna` at reasoning effort high in Docker. With `--evidence raw`, the default, the agent reads `data/input` read-only, without `perun/`, and the URL index `data-sources-scraping.jsonl`; it can reach only OpenRouter and PyPI. It writes its answer to `answer.md`.

`judge.py` then grades every answer by the set's rubrics with `openai/gpt-6-luna-decisions` on OpenRouter's decisions API. A verdict with a confidence below 0.8 is graded again by `openai/gpt-6.1-sol` at reasoning effort high. Each trial in `eval/results/<job>/` keeps its `judgement.json`, and the script prints a score table. Each choice of `--questions` and `--repeats` is its own job, such as `atlas_261110-v1__raw__gpt-6-luna__006-007-x3`. Rerunning the same command resumes unfinished trials and grades again only answers whose inputs changed.

Evidence modes are entries of `EVIDENCE` in `run.py`. A mode returns the agent's mounts or services and the prompt that describes its evidence; a mode for the graph that biotope builds goes there.

The script needs `OPENROUTER_API_KEY` in `.env`, Docker and the pulled data snapshot.

## Push to Argilla

```bash
uv run src/eval/push_argilla.py eval/cqs/atlas_261110
```

The script needs `ARGILLA_API_KEY` (an owner key) in `.env`. It writes to the `elixir-atlas` workspace on `https://test.senantix.com`, in a dataset named `<set-id>-v<version>`, and creates both if needed. Rerunning it updates that dataset from the YAMLs: changed questions are updated, new ones are added and deleted ones are removed.

Once annotators have started, do not edit a version in place. Raise `version` in `set.yaml` and rerun; the new questions go to a new dataset, and the old dataset keeps its responses.
