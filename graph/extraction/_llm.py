import json
import os
import threading
import time
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, cast

import httpx
from biotope.extraction import Document, ExtractionError, Extractor, Field, Schema

from ..paths import PROJECT_ROOT
from ._reading import document_text, squashed, url_of

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-6.1-terra"
CHUNK_CHARS = 60_000
PREFACE_CHARS = 3_000
LOCK = threading.Lock()

SYSTEM = """You extract records for the ELIXIR Atlas, a database about ELIXIR, the European infrastructure for \
life-science data: its Nodes, Hub, Communities, Platforms, Focus Groups, projects and people.

Return every record the schema asks for that this document states, and nothing else.
- Use only what this document states. Never add outside knowledge or guesses. Leave a value null, or a list empty, \
when the document does not state it.
- Copy names, titles, roles and organisation names as the document writes them.
- Write dates as YYYY, YYYY-MM or YYYY-MM-DD, with only the precision the document gives.
- "evidence" is one verbatim excerpt of the document, at most 400 characters, that supports the record. Copy it \
exactly as the text reads, without adding anything.
- "page" is the number in the nearest preceding "[page N]" marker, or null when the document has no markers.
- When only part of a long document is shown, extract the records from that part only.

Schema {name}: {description}

{instructions}"""


@cache
def edam_topics() -> dict[str, str]:
    rows = cast(list[dict[str, str]], json.loads((Path(__file__).with_name("edam_topics.json")).read_text()))
    topics: dict[str, str] = {}
    for row in rows:
        topics.setdefault(row["label"].lower(), row["label"])
    return topics


def topic_instructions() -> str:
    return "EDAM topics to choose from (use these labels exactly): " + "; ".join(sorted(edam_topics().values()))


def field_schema(field: Field) -> dict[str, Any]:
    item: dict[str, Any] = {"type": field.type}
    if field.choices:
        item["enum"] = list(field.choices)
    if field.many:
        return {"type": "array", "items": item, "description": field.description}
    if field.nullable:
        return {"anyOf": [item, {"type": "null"}], "description": field.description}
    return item | {"description": field.description}


def response_format(schema: Schema) -> dict[str, Any]:
    properties = {field.name: field_schema(field) for field in schema.fields}
    properties["evidence"] = {"type": "string", "description": "Verbatim excerpt supporting the record."}
    properties["page"] = {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Page marker number."}
    record = {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
    body = {
        "type": "object",
        "properties": {"records": {"type": "array", "items": record}},
        "required": ["records"],
        "additionalProperties": False,
    }
    return {"type": "json_schema", "json_schema": {"name": schema.name, "strict": True, "schema": body}}


def chunks(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + CHUNK_CHARS)
        if end < len(text):
            cut = text.rfind("\n[page ", start + CHUNK_CHARS // 2, end)
            end = cut if cut > 0 else text.rfind("\n", start + CHUNK_CHARS // 2, end)
        parts.append(text[start:end] if start == 0 else text[:PREFACE_CHARS] + "\n[...]\n" + text[start:end])
        start = end
    return parts


def clean(value: object, field: Field) -> object:
    if isinstance(value, str):
        value = " ".join(value.split()) or None
    if value is None:
        return None
    if field.choices and value not in field.choices:
        raise ExtractionError(f"{field.name}: {value!r} is not one of {field.choices}")
    return value


class LlmExtractor(Extractor):
    instructions: ClassVar[str] = ""
    uses_topics: ClassVar[bool] = False
    max_topics: ClassVar[int] = 6

    def __init__(self) -> None:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ExtractionError("OPENROUTER_API_KEY is not set")
        self.key = key
        self.usage_log = os.environ.get("ATLAS_USAGE_LOG")

    def ask(self, schema: Schema, document: Document, text: str) -> list[dict[str, Any]]:
        instructions = self.instructions + ("\n\n" + topic_instructions() if self.uses_topics else "")
        system = SYSTEM.format(name=schema.name, description=schema.description, instructions=instructions)
        relative = document.path.relative_to(PROJECT_ROOT).as_posix()
        user = f"Document: {relative}\nURL: {url_of(document.path) or 'unknown'}\n\n{text}"
        payload = {
            "model": self.settings["model"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": response_format(schema),
            "reasoning": {"effort": self.settings["reasoning"]},
            "usage": {"include": True},
        }
        for attempt in range(5):
            try:
                response = httpx.post(
                    ENDPOINT, json=payload, headers={"Authorization": f"Bearer {self.key}"}, timeout=900
                )
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError("retry", request=response.request, response=response)
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                self.log(relative, schema.name, body.get("usage") or {})
                return cast(list[dict[str, Any]], json.loads(content)["records"])
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as error:
                if attempt == 4:
                    raise ExtractionError(f"{relative}: {error}") from error
                time.sleep(10 * (attempt + 1))
        raise ExtractionError(f"{relative}: no response")

    def log(self, document: str, schema: str, usage: dict[str, Any]) -> None:
        if not self.usage_log:
            return
        row = {"document": document, "schema": schema} | {
            key: usage.get(key) for key in ("prompt_tokens", "completion_tokens", "cost")
        }
        with LOCK, open(self.usage_log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")

    def extract(self, document: Document, schema: Schema) -> list[dict[str, Any]]:
        text = document_text(document.path)
        if len(text.strip()) < 40:
            raise ExtractionError(f"{document.path.name}: no readable text")
        haystack = squashed(text)
        merged: dict[tuple[object, ...], dict[str, Any]] = {}
        for part in chunks(text):
            for raw in self.ask(schema, document, part):
                record = self.convert(raw, schema, haystack)
                key = tuple(record[name]["value"] for name in schema.key)
                if key in merged:
                    self.merge(merged[key], record, schema)
                else:
                    merged[key] = record
        return list(merged.values())

    def convert(self, raw: dict[str, Any], schema: Schema, haystack: str) -> dict[str, Any]:
        quote = " ".join(str(raw.get("evidence") or "").split())
        found = bool(quote) and squashed(quote)[:120] in haystack
        evidence: dict[str, Any] = {"quote": quote} if found else {}
        page = raw.get("page")
        locator = f"page {page}" if isinstance(page, int) else None
        if locator or not found:
            evidence["locator"] = locator or "quote not found verbatim"
        record: dict[str, Any] = {}
        for field in schema.fields:
            value = raw.get(field.name)
            if field.many:
                items = [clean(item, field) for item in cast(list[object], value or [])]
                values = list(dict.fromkeys(item for item in items if item is not None))
                if field.name == "topics":
                    values = [edam_topics()[v.lower()] for v in values if isinstance(v, str) and v.lower() in edam_topics()]
                    values = values[: self.max_topics]
                record[field.name] = [{"value": item} | evidence for item in values]
            else:
                cleaned = clean(value, field)
                if cleaned is None and not field.nullable:
                    raise ExtractionError(f"{field.name} is required but the model returned none")
                record[field.name] = {"value": cleaned} | evidence
        return record

    def merge(self, kept: dict[str, Any], other: dict[str, Any], schema: Schema) -> None:
        for field in schema.fields:
            if field.many:
                known = {item["value"] for item in kept[field.name]}
                kept[field.name] += [item for item in other[field.name] if item["value"] not in known]
            elif kept[field.name]["value"] is None and other[field.name]["value"] is not None:
                kept[field.name] = other[field.name]

