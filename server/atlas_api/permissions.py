import os

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from .update_requests import COLUMNS, DDL, check_database


def grant_reader(connection, namespace, reader):
    connection.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(namespace), sql.Identifier(reader)))
    connection.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(sql.Identifier(namespace), sql.Identifier(reader)))


def provision(admin_url, reader_url, request_writer=False):
    reader = conninfo_to_dict(reader_url)
    admin = conninfo_to_dict(admin_url)
    if any(reader.get(key) != admin.get(key) for key in ("host", "port", "dbname")):
        raise ValueError("Admin and reader URLs must identify the same database")
    name = reader.get("user")
    if not name or name == admin.get("user") or not reader.get("password"):
        raise ValueError("Supply a distinct reader login and password")
    with psycopg.connect(admin_url) as connection:
        existing = connection.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (name,)).fetchone()
        if not existing:
            connection.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
        connection.execute(sql.SQL("ALTER ROLE {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}").format(sql.Identifier(name), sql.Literal(reader["password"])))
        connection.execute(sql.SQL("REVOKE CREATE, TEMPORARY ON DATABASE {} FROM PUBLIC").format(sql.Identifier(reader["dbname"])))
        connection.execute(sql.SQL("REVOKE CREATE, TEMPORARY ON DATABASE {} FROM {}").format(sql.Identifier(reader["dbname"]), sql.Identifier(name)))
        connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        connection.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM {}").format(sql.Identifier(name)))
        connection.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(reader["dbname"]), sql.Identifier(name)))
        for setting, value in {"default_transaction_read_only": "off" if request_writer else "on", "statement_timeout": "5s", "lock_timeout": "500ms", "idle_in_transaction_session_timeout": "10s", "work_mem": "8MB", "temp_file_limit": "64MB", "max_parallel_workers_per_gather": "0"}.items():
            connection.execute(sql.SQL("ALTER ROLE {} SET {} TO {}").format(sql.Identifier(name), sql.Identifier(setting), sql.Literal(value)))
        if request_writer:
            connection.execute(DDL)
            connection.execute(sql.SQL("GRANT USAGE ON SCHEMA atlas_feedback TO {}").format(sql.Identifier(name)))
            connection.execute(sql.SQL("GRANT INSERT ({}) ON atlas_feedback.update_request TO {}").format(
                sql.SQL(", ").join(map(sql.Identifier, COLUMNS)), sql.Identifier(name)))
        elif connection.execute("SELECT to_regclass('atlas.release')").fetchone()[0]:
            grant_reader(connection, "atlas", name)


def check_reader(connection):
    check_role(connection)


def check_role(connection, request_writer=False):
    unsafe = connection.execute("""
        SELECT current_user <> session_user
            OR EXISTS (SELECT FROM pg_roles WHERE rolname=current_user AND
                (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
            OR EXISTS (SELECT FROM pg_roles WHERE rolname<>current_user AND pg_has_role(current_user, oid, 'MEMBER'))
            OR has_database_privilege(current_database(), 'CREATE,TEMP')
            OR EXISTS (SELECT FROM pg_database WHERE datname=current_database()
                AND datdba=(SELECT oid FROM pg_roles WHERE rolname=current_user))
            OR EXISTS (SELECT FROM pg_namespace WHERE has_schema_privilege(oid, 'CREATE')
                OR nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user))
            OR EXISTS (SELECT FROM pg_class WHERE relkind='S' AND
                (relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)
                    OR has_sequence_privilege(oid, 'USAGE,UPDATE')))
            OR EXISTS (SELECT FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema') AND c.relkind IN ('r','p','v','m','f')
                AND (c.relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)
                    OR has_table_privilege(c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                    OR has_any_column_privilege(c.oid, 'UPDATE')
                    OR EXISTS (SELECT FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
                        AND has_column_privilege(c.oid, a.attnum, 'INSERT')
                        AND NOT (%s AND n.nspname='atlas_feedback' AND c.relname='update_request' AND a.attname=ANY(%s)))))
            OR EXISTS (SELECT FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='atlas')
            OR EXISTS (SELECT FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                WHERE n.nspname<>'pg_catalog' AND p.prosecdef AND has_schema_privilege(n.oid, 'USAGE')
                AND has_function_privilege(p.oid, 'EXECUTE'))
            OR EXISTS (SELECT FROM pg_operator o JOIN pg_namespace n ON n.oid=o.oprnamespace WHERE n.nspname='atlas')
        AS unsafe
    """, (request_writer, list(COLUMNS))).fetchone()
    if unsafe["unsafe"]:
        if request_writer:
            raise RuntimeError("ATLAS_REQUEST_DATABASE_URL must use a dedicated non-owner login with only request-column INSERT privileges")
        raise RuntimeError("DATABASE_URL must use a dedicated non-owner reader with no write, create or role-switch privileges; atlas must contain no custom routines or operators")
    if request_writer:
        readable = connection.execute("SELECT has_any_column_privilege('atlas_feedback.update_request', 'SELECT') AS readable").fetchone()
        if readable["readable"]:
            raise RuntimeError("The request submission login must not read submitted reports")
        allowed = connection.execute("SELECT bool_and(has_column_privilege('atlas_feedback.update_request', name, 'INSERT')) AS allowed FROM unnest(%s::text[]) AS name", (list(COLUMNS),)).fetchone()
        if not allowed["allowed"]:
            raise RuntimeError("Request submission permissions have not been provisioned")


def main():
    writer_url = os.environ.get("ATLAS_REQUEST_DATABASE_URL")
    if writer_url:
        check_database(os.environ["DATABASE_URL"], writer_url)
    provision(os.environ["DATABASE_ADMIN_URL"], os.environ["DATABASE_URL"])
    if writer_url:
        provision(os.environ["DATABASE_ADMIN_URL"], writer_url, request_writer=True)
    print("Reader permissions configured")


if __name__ == "__main__":
    main()
