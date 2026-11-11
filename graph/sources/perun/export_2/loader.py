from collections.abc import Iterator
from pathlib import Path

from biotope.graph import RunContext, SourceRecord

from .._files import optional, read_csv
from . import SOURCE
from .schema import PerunAccount2


def _decode(row: dict[str, str]) -> PerunAccount2:
    return PerunAccount2(
        type=row["type"],
        person_name=row["fullName"],
        status=row["status"],
        group_status=row["groupStatus"],
        organization=optional(row["organization"], PerunAccount2.__missing_values__),
        email=row["email"],
        logins=row["logins"],
        lifescienceid_username=row["lifescienceid-username"],
    )


def _read(path: Path) -> Iterator[SourceRecord[PerunAccount2]]:
    return read_csv(path, PerunAccount2.__record_set__, _decode)


def load(context: RunContext) -> Iterator[SourceRecord[PerunAccount2]]:
    yield from context.load(SOURCE, _read, SOURCE.path())
