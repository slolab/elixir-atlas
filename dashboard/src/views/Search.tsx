import { useState } from "react";
import { Empty, RequestState, SourceLink } from "../components";
import { apiUrl, useApi } from "../db";
import { label, period } from "../format";
import { href, recordHref, typeLabel } from "../route";
import type { Listed, SearchData } from "../types";

export function Search({ query }: { query: string }) {
  const term = query.trim();
  return term.length < 2 ? <Empty>Type at least two characters to search names, descriptions and source evidence.</Empty> : <Results query={term} key={term} />;
}

function Results({ query }: { query: string }) {
  const [type, setType] = useState("");
  const [offset, setOffset] = useState(0);
  const { data, error } = useApi<SearchData>(apiUrl("search", { q: query, limit: 30, offset, ...(type ? { type } : {}) }), 180);
  return (
    <div className="search-results">
      <h1 className="page-title">Results for “{query}”</h1>
      <p className="lede">Search names, descriptions and evidence across the atlas. Names and acronyms rank first. Use quotes for a phrase.</p>
      <label className="filter search-type">Record type
        <select value={type} onChange={(event) => { setType(event.target.value); setOffset(0); }}>
          <option value="">All types</option>
          {type && !data?.facets.some((facet) => facet.entity_type === type) ? <option value={type}>{typeLabel(type)}</option> : null}
          {data?.facets.map((facet) => <option key={facet.entity_type} value={facet.entity_type}>{typeLabel(facet.entity_type)} ({facet.count.toLocaleString("en")})</option>)}
        </select>
      </label>
      {!data ? <RequestState error={error} /> : <>
        <p className="note" role="status">{data.total.toLocaleString("en")} matching records</p>
        {data.hits.length ? <ol className="search-hits">
          {data.hits.map((hit) => <li key={`${hit.entity_type}/${hit.id}`}>
            <span className="kind">{typeLabel(hit.entity_type)}</span>
            <h2><a href={recordHref(hit.entity_type, hit.id)}>{hit.title}</a></h2>
            <p>{hit.excerpt}{hit.excerpt.length >= 320 ? "…" : ""}</p>
            <div className="search-links"><a href={href("record", `${hit.entity_type}/${hit.id}`)}>Record and evidence</a><SourceLink url={hit.url} /></div>
          </li>)}
        </ol> : <Empty>No matching records. Try a name, acronym or shorter phrase.</Empty>}
        <div className="pagination">
          <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 30))}>Previous</button>
          <span>{data.total ? `${offset + 1}–${Math.min(offset + 30, data.total)} of ${data.total.toLocaleString("en")}` : "0 results"}</span>
          <button type="button" disabled={offset + 30 >= data.total} onClick={() => setOffset(offset + 30)}>Next</button>
        </div>
      </>}
    </div>
  );
}

export function KindList({ kind }: { kind: string }) {
  const { data: items, error } = useApi<Listed[]>(apiUrl("kind", { id: kind }));
  if (!items) return <RequestState error={error} />;
  return (
    <>
      <h1 className="page-title">{label(kind)}</h1>
      <p className="lede">{items.length} in the atlas, with the people, Nodes and plan items each one has.</p>
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Period</th>
            <th scope="col" className="number">People</th>
            <th scope="col" className="number">Nodes</th>
            <th scope="col" className="number">Plan items</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                <a href={href("initiative", item.id)}>{item.name}</a>
              </td>
              <td className="nowrap muted">{period(item.start, item.end)}</td>
              <td className="number">{item.people || ""}</td>
              <td className="number">{item.nodes || ""}</td>
              <td className="number">{item.plan || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
