import os
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict

from .import_release import import_release, verify_release


def main():
    path = Path(os.environ.get("ATLAS_RELEASE_DIR", "/app/release"))
    manifest = verify_release(path)
    database_url = os.environ["DATABASE_ADMIN_URL"]
    with psycopg.connect(database_url) as connection:
        exists = connection.execute("SELECT to_regclass('atlas.release')").fetchone()[0]
        current = connection.execute("SELECT manifest FROM atlas.release").fetchone()[0] if exists else None
    if current != manifest:
        reader = conninfo_to_dict(os.environ["DATABASE_URL"])["user"]
        result = import_release(path, database_url, reader=reader)
        print(f"Imported release {result['release']}: {result['records']} records")
    else:
        print(f"Release {manifest['id']} already loaded")


if __name__ == "__main__":
    main()
