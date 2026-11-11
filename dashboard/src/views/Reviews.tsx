import type { ReviewsData } from "../types";
import { useState } from "react";
import { Empty, RequestState, EntityLink, More, SourceLink } from "../components";
import { apiUrl, useApi, list, type Row } from "../db";
import { label, text } from "../format";
import { href } from "../route";

export function Reviews({ kind }: { kind: string }) {
  const [filter, setFilter] = useState("");
  const { data, error } = useApi<ReviewsData>(apiUrl("reviews", { kind }));
  if (!data) return <RequestState error={error} />;
  const { kinds, active, items } = data;
  const needle = filter.trim().toLowerCase();
  const shown = needle ? items.filter((item) => `${text(item.question)} ${text(item.subject_names)}`.toLowerCase().includes(needle)) : items;
  return (
    <>
      <h1 className="page-title">Review queue</h1>
      <p className="lede">
        Each item is a question the sources could not settle. The queue is read-only; reviewed decisions are included in a future data release.
      </p>
      <nav className="tabs" aria-label="Kinds of review item">
        {kinds.map((entry) => (
          <a key={entry.kind} href={href("reviews", entry.kind)} aria-current={entry.kind === active ? "page" : undefined}>
            {label(entry.kind)} <span className="count">{entry.n}</span>
          </a>
        ))}
      </nav>
      <label className="filter">
        <span className="visually-hidden">Filter by name</span>
        <input type="search" placeholder="Filter by name or text" value={filter} onChange={(event) => setFilter(event.target.value)} />
      </label>
      {shown.length ? <More items={shown} limit={40} render={(page) => <ReviewList items={page} />} /> : <Empty>No open items match.</Empty>}
    </>
  );
}

export function ReviewList({ items }: { items: Row[] }) {
  return (
    <ol className="reviews">
      {items.map((item) => {
        const subjects = list(item.subjects);
        const names = list(item.subject_names);
        return (
          <li key={text(item.id)}>
            <p className="question">{text(item.question)}</p>
            <p className="subjects">
              {subjects.map((subject, index) => (
                <span key={subject}>
                  {index ? <span className="muted"> or </span> : null}
                  <EntityLink id={subject}>{names[index] ?? subject}</EntityLink>
                </span>
              ))}
            </p>
            <ul className="options">
              {list(item.options).map((option) => {
                const [value, sources = ""] = option.split(" | ");
                return (
                  <li key={option}>
                    <span className="option-value">{value}</span>
                    {sources
                      .split(", ")
                      .filter(Boolean)
                      .map((url) => (
                        <SourceLink key={url} url={url} full />
                      ))}
                  </li>
                );
              })}
            </ul>
            <p className="review-id">
              <span className="muted">Item id </span>
              <code>{text(item.id)}</code>
            </p>
          </li>
        );
      })}
    </ol>
  );
}
