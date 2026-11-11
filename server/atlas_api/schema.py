import re

import yaml


TYPES = {"str": "text", "str[]": "text[]", "int": "bigint", "float": "double precision", "bool": "boolean"}


def identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid SQL identifier: {value}")
    return '"' + value + '"'


def read_schema(path):
    schema = yaml.safe_load(path.read_text())
    for name, entity in schema.items():
        identifier(name)
        if entity["represented_as"] not in {"node", "edge"}:
            raise ValueError(f"Unsupported entity: {name}")
        for column, kind in entity["properties"].items():
            identifier(column)
            if kind not in TYPES:
                raise ValueError(f"Unsupported type: {name}.{column}: {kind}")
        if entity["represented_as"] == "edge":
            for end in ("source", "target"):
                if schema[entity[end]]["represented_as"] != "node":
                    raise ValueError(f"Invalid endpoint: {name}.{end}")
    if len({name.lower() for name in schema}) != len(schema):
        raise ValueError("Table names collide after lowercasing")
    return schema


def ordered_tables(schema):
    return sorted(schema, key=lambda name: (schema[name]["represented_as"] == "edge", name))


def sql_schema(schema):
    tables = {}
    for name in ordered_tables(schema):
        entity = schema[name]
        metadata = entity.get("biotope", {})
        columns = {"id": {"type": "text", "nullable": False, "description": "Stable record identifier.", "primary_key": True}}
        if entity["represented_as"] == "edge":
            for end in ("source", "target"):
                columns[end] = {"type": "text", "nullable": False, "references": f"atlas.{entity[end].lower()}.id", "description": f"The {end} endpoint ({entity[end]})."}
        for column, kind in entity["properties"].items():
            columns[column] = {"type": TYPES[kind], "nullable": column in metadata.get("nullable", []), "description": metadata.get("property_descriptions", {}).get(column, "")}
            if column == "biotope_provenance_id":
                columns[column].update(references="atlas.provenance.id", description="Source evidence and mapping identifiers for this record.")
        tables[f"atlas.{name.lower()}"] = {"concept": name, "kind": entity["represented_as"], "description": entity.get("description", ""), "columns": columns}
    tables["atlas.provenance"] = {"description": "Build evidence for a record. Internal artifact paths identify provenance, not public citations; use source URLs and DOIs for citations.", "columns": {
        "id": {"type": "bigint", "nullable": False, "primary_key": True},
        "data": {"type": "jsonb", "nullable": False, "description": "mappings and evidence entries with source artifact, version and location."},
    }}
    return tables


def ddl(schema, namespace="atlas"):
    ns = identifier(namespace)
    statements = [
        f"CREATE SCHEMA {ns}",
        f"CREATE TABLE {ns}.provenance (id bigint PRIMARY KEY, data jsonb NOT NULL)",
        f"CREATE TABLE {ns}.release (id text PRIMARY KEY, manifest jsonb NOT NULL, topology jsonb NOT NULL, counts jsonb NOT NULL, imported_at timestamptz NOT NULL DEFAULT now())",
    ]
    for name in ordered_tables(schema):
        entity = schema[name]
        table = f"{ns}.{identifier(name.lower())}"
        columns = ['"id" text PRIMARY KEY']
        if entity["represented_as"] == "edge":
            for endpoint in ("source", "target"):
                target = identifier(entity[endpoint].lower())
                columns.append(f'{identifier(endpoint)} text NOT NULL REFERENCES {ns}.{target}(id)')
        for column, kind in entity["properties"].items():
            nullable = column in entity.get("biotope", {}).get("nullable", [])
            definition = f"{identifier(column)} {TYPES[kind]}" + ("" if nullable else " NOT NULL")
            if column == "biotope_provenance_id":
                definition += f" REFERENCES {ns}.provenance(id)"
            columns.append(definition)
        statements.append(f"CREATE TABLE {table} (" + ", ".join(columns) + ")")
        if entity["represented_as"] == "edge":
            for endpoint in ("source", "target"):
                statements.append(f"CREATE INDEX ON {table} ({identifier(endpoint)})")
    statements.extend([
        f"""CREATE TABLE {ns}.search_document (
            entity_type text NOT NULL,
            id text NOT NULL,
            title text NOT NULL,
            names text NOT NULL,
            body text NOT NULL,
            url text,
            document tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('simple', names), 'A') ||
                setweight(to_tsvector('english', body), 'B')
            ) STORED,
            PRIMARY KEY (entity_type, id)
        )""",
        f"CREATE INDEX ON {ns}.search_document USING gin(document)",
        f"CREATE INDEX ON {ns}.search_document USING gin(names gin_trgm_ops)",
        f"CREATE INDEX ON {ns}.search_document USING gin(title gin_trgm_ops)",
    ])
    return ";\n".join(statements) + ";\n"
