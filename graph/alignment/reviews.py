from dataclasses import dataclass

from .names import digest, list_item


@dataclass(frozen=True)
class Review:
    review_id: str
    kind: str
    question: str
    subjects: tuple[str, ...]
    subject_names: tuple[str, ...]
    property: str | None
    options: tuple[str, ...]
    status: str = "open"
    decision: str | None = None


def review_id(kind: str, subjects: list[str], prop: str | None = None) -> str:
    return f"review:{kind}:{digest(kind, prop or '', *sorted(set(subjects)))}"


def review(
    kind: str,
    question: str,
    subjects: list[str],
    names: list[str],
    options: list[str],
    prop: str | None = None,
) -> Review:
    ordered = sorted(set(subjects))
    return Review(
        review_id=review_id(kind, ordered, prop),
        kind=kind,
        question=" ".join(question.split()),
        subjects=tuple(ordered),
        subject_names=tuple(list_item(name) for name in names),
        property=prop,
        options=tuple(dict.fromkeys(list_item(option) for option in options)),
    )


def months(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 6
    except ValueError:
        return None
    return year * 12 + month


def span(value: str) -> tuple[int, int] | None:
    point = months(value)
    if point is None:
        return None
    return (point - 5, point + 6) if len(value.split("-")) == 1 else (point, point)


def dates_agree(values: list[str]) -> bool:
    spans = [found for found in (span(value) for value in values) if found is not None]
    return not spans or max(low for low, _ in spans) - min(high for _, high in spans) <= 1


def agreed_date(values: list[str]) -> str | None:
    known = [value for value in values if months(value) is not None]
    if not known or not dates_agree(known):
        return None
    return max(known, key=lambda value: (len(value), value))
