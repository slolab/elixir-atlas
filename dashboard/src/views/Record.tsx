import { useState } from "react";
import { Empty, More, RequestState, Section } from "../components";
import { apiUrl, useApi, type Value } from "../db";
import { label, text } from "../format";
import { href, recordHref, typeLabel } from "../route";
import type { RecordData, RelationsData } from "../types";

function ValueText({ value }: { value: Value }) {
  if (value === null) return <span className="muted">Not recorded</span>;
  if (Array.isArray(value)) return <>{value.length ? value.join("; ") : <span className="muted">None recorded</span>}</>;
  if (typeof value === "boolean") return <>{value ? "Yes" : "No"}</>;
  if (typeof value === "string" && /^https?:\/\//.test(value)) return <a href={value} target="_blank" rel="noreferrer">{value}</a>;
  return <>{String(value)}</>;
}

export function RecordPage({ value }: { value: string }) {
  const [type, ...rest] = value.split("/");
  const id = rest.join("/");
  const { data, error } = useApi<RecordData>(apiUrl("record", { type, id }));
  if (!data) return <RequestState error={error} />;
  const summary = recordHref(type, id);
  return <article className="record-page">
    <header className="entity-head">
      <p className="kind">{typeLabel(type)}</p>
      <h1>{data.title}</h1>
      <p className="summary">{data.definition.description}</p>
      {summary !== href("record", value) ? <a href={summary}>Open dashboard view</a> : null}
    </header>
    <Section title="Record">
      <dl className="record-fields">
        {Object.entries(data.record).filter(([field]) => field !== "biotope_provenance_id").map(([field, value]) => <div key={field}>
          <dt>{label(field)}<p className="note">{data.definition.biotope.property_descriptions[field]}</p></dt>
          <dd>{(field === "source" || field === "target") && data.definition.represented_as === "edge" ? <a href={recordHref(data.definition[field]!, text(value))}>{text(value)}</a> : <ValueText value={value} />}</dd>
        </div>)}
      </dl>
    </Section>
    <Section title="Source evidence" note="Each entry identifies the source version and location used to build this record.">
      <More items={data.provenance.evidence} limit={12} render={(items) => <ol className="evidence-list">{items.map((item, index) => <li key={`${item.artifact}/${item.location}/${index}`}>
        <strong>{item.artifact}</strong><span>{item.location}</span><code>{item.version}</code>
      </li>)}</ol>} />
    </Section>
    {data.definition.represented_as === "node" ? <Relations type={type} id={id} key={`${type}/${id}`} /> : null}
  </article>;
}

function Relations({ type, id }: { type: string; id: string }) {
  const [offset, setOffset] = useState(0);
  const { data, error } = useApi<RelationsData>(apiUrl("relations", { type, id, offset, limit: 30 }));
  return <Section title="Relationships">
    {!data ? <RequestState error={error} /> : data.total === 0 ? <Empty>No relationships recorded.</Empty> : <>
      <ul className="hits">{data.items.map((item) => <li key={`${item.relation_type}/${item.relation_id}/${item.direction}`}>
        <a href={recordHref(item.entity_type, item.id)}>{item.title}</a>
        <a className="kind" href={href("record", `${item.relation_type}/${item.relation_id}`)}>{typeLabel(item.relation_type)} · {item.direction}</a>
      </li>)}</ul>
      <div className="pagination">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 30))}>Previous</button>
        <span>{offset + 1}–{Math.min(offset + 30, data.total)} of {data.total}</span>
        <button disabled={offset + 30 >= data.total} onClick={() => setOffset(offset + 30)}>Next</button>
      </div>
    </>}
  </Section>;
}
