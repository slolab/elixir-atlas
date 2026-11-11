import { useMemo, useState } from "react";
import { Empty, EntityLink, More, SourceLink } from "../components";
import { list, rows, type Row } from "../db";
import { label, text } from "../format";
import { href } from "../route";

export function Reviews({ kind }: { kind: string }) {
  const kinds = useMemo(() => rows<{ kind: string; n: number }>("select kind, count(*) n from ReviewItem where status = 'open' group by kind order by n desc"), []);
  const active = kind || kinds[0]?.kind || "";
  const [filter, setFilter] = useState("");
  const items = useMemo(() => rows("select * from ReviewItem where status = 'open' and kind = ? order by property, question", [active]), [active]);
  const needle = filter.trim().toLowerCase();
  const shown = needle ? items.filter((item) => `${text(item.question)} ${text(item.subject_names)}`.toLowerCase().includes(needle)) : items;
  return (
    <>
      <h1 className="page-title">Review queue</h1>
      <p className="lede">
        Each item is a question the build could not settle from the sources. Write a decision in data/input/review-decisions.csv, with the item id and either same, different, the correct value or all valid. The next build applies it.
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
