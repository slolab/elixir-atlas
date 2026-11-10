# Evaluation

`user_stories.md` holds the user stories. `cqs/<set-id>/` holds a competency-question (CQ) set, a simplified version of the biotope-bench layout:

- `set.yaml`: the set's `id`, its `version`, the users' `purpose`, the data snapshot it was written against (`reference_dataset`), the `context` that answering agents see and the `rubric`: `correctness` and `sources`.
- `questions/<set-id>-NNN.yaml`: one question with its `user_story`, `question`, `answerability`, `reference_answer`, `eval_notes` (the components the rubrics score) and `sources` (paths under `data/`).
- `sidenotes.md`: how the answers were derived, data-quality notes and details left out of the answers.

The rubrics measure accuracy: whether the answer's facts are correct, and whether each one cites a source that exists, holds the fact and bears on the question. Argilla collects how users like the answers: annotators see each question with its reference answer, rate it from 1 to 5 and can leave feedback.

## Push to Argilla

```bash
uv run eval/push_argilla.py eval/cqs/atlas_261110
```

The script needs `ARGILLA_API_KEY` (an owner key) in `.env`. It writes to the `elixir-atlas` workspace on `https://test.senantix.com`, in a dataset named `<set-id>-v<version>`, and creates both if needed. Rerunning it updates that dataset from the YAMLs: changed questions are updated, new ones are added and deleted ones are removed.

Once annotators have started, do not edit a version in place. Raise `version` in `set.yaml` and rerun; the new questions go to a new dataset, and the old dataset keeps its responses.
