from typing import Literal
from uuid import uuid4

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


COLUMNS = ("id", "release_id", "origin", "entity_type", "entity_id", "message", "proposed_change", "evidence", "context")
DDL = """
CREATE SCHEMA IF NOT EXISTS atlas_feedback;
CREATE TABLE IF NOT EXISTS atlas_feedback.update_request (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    status text NOT NULL DEFAULT 'pending' CHECK (status = 'pending'),
    release_id text NOT NULL,
    origin text NOT NULL CHECK (origin IN ('dashboard', 'agent')),
    entity_type text,
    entity_id text,
    message text NOT NULL CHECK (length(btrim(message)) BETWEEN 1 AND 5000),
    proposed_change text NOT NULL CHECK (length(proposed_change) <= 5000),
    evidence text NOT NULL CHECK (length(evidence) <= 5000),
    context text NOT NULL CHECK (length(context) <= 10000),
    CHECK ((entity_type IS NULL) = (entity_id IS NULL))
);
REVOKE ALL ON SCHEMA atlas_feedback FROM PUBLIC;
REVOKE ALL ON atlas_feedback.update_request FROM PUBLIC;
"""


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    origin: Literal["dashboard", "agent"]
    entity_type: str | None = Field(default=None, min_length=1, max_length=100)
    entity_id: str | None = Field(default=None, min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=5000)
    proposed_change: str = Field(default="", max_length=5000)
    evidence: str = Field(default="", max_length=5000)
    context: str = Field(default="", max_length=10000)

    @field_validator("*")
    @classmethod
    def valid_text(cls, value):
        if isinstance(value, str):
            if "\x00" in value:
                raise ValueError("Text must not contain null characters")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValueError("Text must be valid UTF-8") from error
        return value

    @model_validator(mode="after")
    def paired_target(self):
        if (self.entity_type is None) != (self.entity_id is None):
            raise ValueError("Supply both entity_type and entity_id, or neither")
        return self


def check_database(reader_url, writer_url):
    reader, writer = map(conninfo_to_dict, (reader_url, writer_url))
    if any(reader.get(key) != writer.get(key) for key in ("host", "port", "dbname")):
        raise ValueError("Request submissions must use the same database as the Atlas reader")
    if reader.get("user") == writer.get("user"):
        raise ValueError("Request submissions require a separate login")


def insert_request(connection, body, release_id):
    identifier = uuid4()
    values = {"id": identifier, "release_id": release_id, **body.model_dump()}
    connection.execute(
        sql.SQL("INSERT INTO atlas_feedback.update_request ({}) VALUES ({})").format(
            sql.SQL(", ").join(map(sql.Identifier, COLUMNS)),
            sql.SQL(", ").join(sql.Placeholder() for _ in COLUMNS),
        ),
        tuple(values[column] for column in COLUMNS),
    )
    return {"id": str(identifier), "status": "pending"}
