# /// script
# requires-python = ">=3.11"
# dependencies = ["argilla==2.8.0", "python-dotenv", "pyyaml", "requests"]
# ///

import os
import sys
from pathlib import Path

import argilla as rg
import yaml
from dotenv import load_dotenv

API_URL = "https://test.senantix.com"
WORKSPACE = "elixir-atlas"
RESPONSES_PER_RECORD = 3


def settings():
    return rg.Settings(
        guidelines=(
            "Read the question and the answer. Rate the answer from 1 to 5 by your own judgement. "
            "Tell us anything you think in the feedback box."
        ),
        distribution=rg.TaskDistribution(min_submitted=RESPONSES_PER_RECORD),
        fields=[
            rg.TextField(name="question", title="Question", use_markdown=True),
            rg.TextField(name="answer", title="Answer", use_markdown=True),
        ],
        questions=[
            rg.RatingQuestion(name="rating", title="How would you rate this answer?", values=[1, 2, 3, 4, 5]),
            rg.TextQuestion(name="feedback", title="Feedback", required=False),
        ],
    )


def main(folder):
    cq_set = yaml.safe_load((folder / "set.yaml").read_text())
    questions = [yaml.safe_load(path.read_text()) for path in sorted((folder / "questions").glob("*.yaml"))]
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    client = rg.Argilla(api_url=API_URL, api_key=os.environ["ARGILLA_API_KEY"])
    if client.workspaces(WORKSPACE) is None:
        rg.Workspace(name=WORKSPACE, client=client).create()
    name = f"{cq_set['id']}-v{cq_set['version']}"
    dataset = client.datasets(name=name, workspace=WORKSPACE)
    if dataset is None:
        dataset = rg.Dataset(name=name, workspace=WORKSPACE, settings=settings(), client=client).create()
    dataset.records.log([
        rg.Record(id=q["id"], fields={"question": q["question"], "answer": q["reference_answer"]})
        for q in questions
    ])
    ids = {q["id"] for q in questions}
    stale = [record for record in dataset.records if record.id not in ids]
    if stale:
        dataset.records.delete(stale)
    print(f"{WORKSPACE}/{name}: {len(questions)} records, {len(stale)} removed")
    print(f"{API_URL}/dataset/{dataset.id}/annotation-mode")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
