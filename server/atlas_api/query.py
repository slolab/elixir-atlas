import json
import time

from fastapi.encoders import jsonable_encoder
from pglast.parser import ParseError, parse_sql_json
from psycopg.rows import tuple_row


MAX_ROWS = 1000
MAX_BYTES = 1_000_000
TIMEOUT_MS = 5000
FUNCTIONS = set("""
abs age array_agg array_length array_lower array_position array_remove array_to_string array_upper
avg bit_and bit_or bool_and bool_or btrim cardinality ceil ceiling char_length concat concat_ws
count date date_part date_trunc dense_rank every extract first_value floor greatest
json_agg json_array_length json_build_array json_build_object json_each json_each_text
json_extract_path json_extract_path_text json_object_agg json_typeof
jsonb_agg jsonb_array_elements jsonb_array_elements_text jsonb_array_length jsonb_build_array
jsonb_build_object jsonb_each jsonb_each_text jsonb_extract_path jsonb_extract_path_text
jsonb_object_agg jsonb_object_keys jsonb_typeof lag last_value lead least left length lower
ltrim make_date max min now nth_value ntile octet_length position rank regexp_match
regexp_matches regexp_replace regexp_split_to_array regexp_split_to_table replace right round
row_number row_to_json rtrim split_part starts_with string_agg string_to_array strpos substr
substring sum timezone to_char to_date to_json to_jsonb to_number to_timestamp translate trim
trunc unnest upper
""".split())
TYPES = set("text varchar bpchar name bool boolean int2 int4 int8 smallint integer bigint float4 float8 real numeric decimal date time timetz timestamp timestamptz interval json jsonb uuid".split())
NODES = set("""
SelectStmt ResTarget ColumnRef A_Star A_Const Integer Float Boolean String BitString
RangeVar RangeSubselect RangeFunction JoinExpr Alias A_Expr BoolExpr NullTest BooleanTest
FuncCall NamedArgExpr TypeCast TypeName CoalesceExpr MinMaxExpr CaseExpr CaseWhen
SubLink RowExpr A_ArrayExpr A_Indirection A_Indices SortBy WindowDef WithClause
CommonTableExpr GroupingSet GroupingFunc SQLValueFunction CollateClause List
""".split())


class QueryError(ValueError):
    def __init__(self, message, code="query_not_allowed", position=None, status=400, hint=None):
        super().__init__(message)
        self.code = code
        self.position = position
        self.status = status
        self.hint = hint


def names(parts):
    return [part["String"]["sval"] for part in parts]


def builtin(parts, allowed, label):
    path = names(parts)
    if not path or len(path) > 2 or (len(path) == 2 and path[0] != "pg_catalog") or path[-1] not in allowed:
        raise QueryError(f"Unsupported {label}: {'.'.join(path)}. See /api/schema?format=sql for supported SQL.")


def validate(query, tables):
    if "\x00" in query:
        raise QueryError("SQL must not contain NUL characters.", "invalid_sql_text")
    try:
        query.encode("utf-8")
    except UnicodeEncodeError as error:
        raise QueryError("SQL must contain valid Unicode text.", "invalid_sql_text") from error
    try:
        statements = json.loads(parse_sql_json(query))["stmts"]
    except ParseError as error:
        position = error.args[1] + 1 if len(error.args) > 1 and isinstance(error.args[1], int) else None
        raise QueryError(error.args[0], "syntax_error", position, hint='Use double quotes for identifiers such as "end" and single quotes for string values. Send the SQL as a JSON string; do not leave placeholders in it.') from error
    if len(statements) != 1 or "SelectStmt" not in statements[0]["stmt"]:
        raise QueryError("Send exactly one SELECT query, optionally with read-only CTEs.")

    def visit(value, ctes=frozenset()):
        if isinstance(value, list):
            for item in value:
                visit(item, ctes)
        elif isinstance(value, dict):
            if "SelectStmt" in value:
                statement = value["SelectStmt"]
                if statement.get("intoClause") or statement.get("lockingClause"):
                    raise QueryError("SELECT INTO and row locking are not allowed.")
                clause = statement.get("withClause", {})
                definitions = clause.get("ctes", [])
                if clause.get("recursive"):
                    ctes = ctes | {item["CommonTableExpr"]["ctename"] for item in definitions}
                for definition in definitions:
                    visit(definition, ctes)
                    ctes = ctes | {definition["CommonTableExpr"]["ctename"]}
                visit({key: item for key, item in statement.items() if key != "withClause"}, ctes)
                return
            for key, item in value.items():
                if key[0].isupper() and key not in NODES:
                    raise QueryError(f"Unsupported SQL construct: {key}.")
                if key == "RangeVar":
                    table = item["relname"]
                    namespace = item.get("schemaname")
                    if item.get("catalogname") or namespace not in (None, "atlas"):
                        raise QueryError("Only the documented Atlas tables are queryable.")
                    if table not in tables and not (namespace is None and table in ctes):
                        raise QueryError(f"Unknown table: {table}. Read /api/schema?format=sql for table names.", "unknown_table")
                elif key == "FuncCall":
                    builtin(item["funcname"], FUNCTIONS, "function")
                elif key == "TypeCast":
                    builtin(item["typeName"]["names"], TYPES, "cast type")
                elif key == "A_Indirection":
                    if any("A_Indices" not in part for part in item["indirection"]):
                        raise QueryError("Computed field notation is not supported; use explicit supported functions.")
                elif key == "RangeFunction":
                    if not item.get("ordinality"):
                        raise QueryError("FROM functions require WITH ORDINALITY, e.g. unnest(tags) WITH ORDINALITY AS u(value, position).")
                    if item.get("coldeflist"):
                        raise QueryError("Typed table-function definitions are not supported.")
                elif key in ("A_Expr", "SortBy"):
                    operator = names(item.get("name" if key == "A_Expr" else "useOp", []))
                    if len(operator) > 1 and (len(operator) != 2 or operator[0] != "pg_catalog"):
                        raise QueryError("Only PostgreSQL built-in operators are allowed.")
                elif key == "CollateClause":
                    builtin(item["collname"], {"C", "POSIX", "default"}, "collation")
                visit(item, ctes)

    visit(statements[0]["stmt"])


def encoded(value):
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    except ValueError as error:
        raise QueryError("The result contains a non-finite number. Cast it to text or filter it out.", "invalid_result", status=422) from error


def execute(db, query, limit, release, api_revision):
    validate(query, {name.lower() for name in release["topology"]} | {"provenance"})
    db.execute("SET LOCAL search_path TO pg_catalog, atlas")
    db.execute(f"SET LOCAL statement_timeout TO '{TIMEOUT_MS}ms'")
    db.execute("SET LOCAL lock_timeout TO '500ms'")
    started = time.monotonic()
    with db.cursor(name="atlas_query", row_factory=tuple_row) as cursor:
        cursor.execute(query)
        result = {
            "release": release["id"], "api_revision": api_revision,
            "schema_sha256": release["manifest"]["files"]["schema_config.yaml"]["sha256"],
            "columns": [], "rows": [], "row_count": 0, "truncated": False,
            "truncation_reason": None, "duration_ms": 0,
        }
        size = 0
        while not result["truncated"]:
            remaining = TIMEOUT_MS - int((time.monotonic() - started) * 1000)
            if remaining <= 0:
                raise QueryError("Query exceeded five seconds. Narrow the query and retry.", "query_timeout", status=408)
            db.execute("SELECT set_config('statement_timeout', %s, true)", (f"{remaining}ms",))
            fetched = cursor.fetchmany(min(16, limit + 1 - len(result["rows"])))
            if not size:
                result["columns"] = [{"name": column.name, "type_oid": column.type_code} for column in cursor.description]
                size = len(encoded(result)) + 256
            if not fetched:
                break
            for row in fetched:
                if len(result["rows"]) == limit:
                    result.update(truncated=True, truncation_reason="rows")
                    break
                row = jsonable_encoder(row)
                row_size = len(encoded(row)) + 1
                if size + row_size > MAX_BYTES:
                    if not result["rows"]:
                        raise QueryError("One result row exceeds 1 MB. Select fewer or shorter fields.", "result_too_large", status=422)
                    result.update(truncated=True, truncation_reason="bytes")
                    break
                result["rows"].append(row)
                size += row_size
    result["row_count"] = len(result["rows"])
    result["duration_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result
