import { type ReactNode, useState } from "react";
import type { Value } from "./db";
import { host, pageLabel, text } from "./format";
import { entityHref } from "./route";

export function EntityLink({ id, children }: { id: Value; children: ReactNode }) {
  const target = entityHref(text(id));
  return target ? <a href={target}>{children}</a> : <>{children}</>;
}

export function SourceLink({ url, retrieved, full }: { url: Value | undefined; retrieved?: Value; full?: boolean }) {
  if (!url) {
    return null;
  }
  const day = text(retrieved).slice(0, 10);
  return (
    <a className="source" href={text(url)} target="_blank" rel="noreferrer" title={day ? `${text(url)}, retrieved ${day}` : text(url)}>
      {full ? pageLabel(url) : host(url)}
    </a>
  );
}

export function Section({ title, note, children, id }: { title: string; note?: string; children: ReactNode; id?: string }) {
  return (
    <section className="section" id={id}>
      <header className="section-head">
        <h2>{title}</h2>
        {note ? <p className="note">{note}</p> : null}
      </header>
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}

export function Table({ children, className = "table" }: { children: ReactNode; className?: string }) {
  return <div className="table-scroll" role="region" aria-label="Scrollable table" tabIndex={0}><table className={className}>{children}</table></div>;
}

export type Fact = [string, ReactNode];

export function Facts({ facts }: { facts: Fact[] }) {
  const shown = facts.filter(([, value]) => value !== "" && value !== null && value !== undefined && value !== false);
  return (
    <dl className="facts">
      {shown.map(([name, value]) => (
        <div key={name}>
          <dt>{name}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export type Bar = { key: string; name: ReactNode; value: number; extra?: ReactNode };

export function Bars({ bars, tone = "ink" }: { bars: Bar[]; tone?: string }) {
  const max = Math.max(1, ...bars.map((bar) => bar.value));
  return (
    <ol className="bars">
      {bars.map((bar) => (
        <li key={bar.key}>
          <span className="bar-name">{bar.name}</span>
          <span className="bar-track" aria-hidden="true">
            <span className={`bar-fill tone-${tone}`} style={{ width: `${(bar.value / max) * 100}%` }} />
          </span>
          <span className="bar-value">{bar.value.toLocaleString("en")}</span>
          {bar.extra ? <span className="bar-extra">{bar.extra}</span> : null}
        </li>
      ))}
    </ol>
  );
}

export function More<T>({ items, limit, render }: { items: T[]; limit: number; render: (shown: T[]) => ReactNode }) {
  return <MoreInner items={items} limit={limit} render={render} key={items.length} />;
}


function MoreInner<T>({ items, limit, render }: { items: T[]; limit: number; render: (shown: T[]) => ReactNode }) {
  const [shown, setShown] = useState(limit);
  return (
    <>
      {render(items.slice(0, shown))}
      {items.length > shown ? (
        <button className="more" type="button" onClick={() => setShown(shown + limit * 4)}>
          {items.length - shown <= limit * 4 ? `Show the other ${items.length - shown}` : `Show ${limit * 4} more of ${items.length - shown}`}
        </button>
      ) : null}
    </>
  );
}

export function RequestState({ error }: { error?: string }) {
  return error ? <div className="status failed" role="alert"><p>{error}</p><button type="button" onClick={() => window.location.reload()}>Try again</button></div> : <p className="status" role="status">Loading atlas records…</p>;
}
