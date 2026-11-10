import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from string import Template

PROMPTS = Path(__file__).resolve().parent / "prompts"
API = "https://openrouter.ai/api"
DECIDER = "openai/gpt-6-luna-decisions"
ESCALATION = "openai/gpt-6.1-sol"
ESCALATION_EFFORT = "high"
MIN_CONFIDENCE = 0.8
SCORES = {"correct": 1, "partial": 0.5, "failed": 0}
CRITERIA = {
    "correct": "The answer meets the rubric's conditions for correct.",
    "partial": "The answer meets the rubric's conditions for partial, but not those for correct.",
    "failed": "The answer meets the rubric's conditions for failed, or does not answer the question.",
}
SCHEMA = {
    "type": "object",
    "properties": {"verdict": {"type": "string", "enum": list(SCORES)}, "explanation": {"type": "string"}},
    "required": ["verdict", "explanation"],
    "additionalProperties": False,
}
RETRY_DELAYS = (5, 30, 120)


def render(name, **values):
    return Template((PROMPTS / name).read_text()).substitute(values)


def post(path, body):
    request = urllib.request.Request(API + path, json.dumps(body).encode(), {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"})
    for delay in (*RETRY_DELAYS, None):
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if delay is None or error.code < 500 and error.code not in (408, 429):
                raise RuntimeError(f"{path}: HTTP {error.code} {error.read().decode(errors='replace')[:300]}")
        except OSError:
            if delay is None:
                raise
        time.sleep(delay)


def escalate(state, rubric, criteria):
    prompt = render("judge.md", **state, rubric=rubric, criteria=criteria)
    response = post("/v1/chat/completions", {
        "model": ESCALATION, "reasoning": {"effort": ESCALATION_EFFORT},
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "grade", "strict": True, "schema": SCHEMA}},
    })
    return json.loads(response["choices"][0]["message"]["content"]), response["usage"].get("cost", 0)


def grade(state, rubrics):
    response = post("/alpha/decisions", {"model": DECIDER, "state": state, "questions": {
        name: {"type": "choice", "instructions": render("decision.md", rubric=name, criteria=criteria),
               "criteria": CRITERIA}
        for name, criteria in rubrics.items()}})
    grades, cost = {}, response["usage"].get("cost", 0)
    for name, criteria in rubrics.items():
        decision = response["answers"][name]
        grades[name] = {"verdict": decision["choice"], "confidence": decision["confidence"], "judge": DECIDER}
        if decision["confidence"] < MIN_CONFIDENCE:
            escalated, escalation_cost = escalate(state, name, criteria)
            grades[name] |= escalated | {"judge": ESCALATION, "decider_verdict": decision["choice"]}
            cost += escalation_cost
    return grades, cost


def judge_trial(trial, question, cq_set):
    answer_path = trial / "artifacts" / "workspace" / "answer.md"
    answer = answer_path.read_text().strip() if answer_path.is_file() else ""
    rubrics = {rubric["name"]: rubric["criteria"].strip() for rubric in cq_set["rubric"]}
    state = {"question": question["question"].strip(), "context": cq_set["context"].strip(),
             "reference_answer": question["reference_answer"].strip(),
             "eval_notes": question["eval_notes"].strip(), "answer": answer}
    inputs = hashlib.sha256(json.dumps([state, rubrics, DECIDER, ESCALATION, MIN_CONFIDENCE]).encode()).hexdigest()
    path = trial / "judgement.json"
    if path.is_file() and json.loads(path.read_text())["inputs_sha256"] == inputs:
        return json.loads(path.read_text())
    if answer:
        grades, cost = grade(state, rubrics)
    else:
        grades, cost = {name: {"verdict": "failed", "judge": None, "explanation": "no answer"} for name in rubrics}, 0
    judgement = {"question": question["id"], "inputs_sha256": inputs, "grades": grades, "cost_usd": cost}
    path.write_text(json.dumps(judgement, indent=2) + "\n")
    return judgement
