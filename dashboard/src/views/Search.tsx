import { useMemo } from "react";
import { Empty, Section } from "../components";
import { rows } from "../db";
import { label, period } from "../format";
import { href } from "../route";

type Hit = { id: string; name: string; kind?: string; acronym?: string };

export function Search({ query }: { query: string }) {
  const term = query.trim();
  const hits = useMemo(() => {
    if (term.length < 2) {
      return null;
    }
    const like = `%${term}%`;
    return {
      initiatives: rows<Hit>(
        `select id, name, kind, acronym from Initiative
         where name like ? or acronym like ? or aliases like ?
         order by (name like ?) desc, (name like ?) desc, length(name) limit 80`,
        [like, like, like, `${term}%`, like],
      ),
      people: rows<Hit>(
        "select id, name from Person where name like ? or name_variants like ? order by (name like ?) desc, name limit 80",
        [like, like, `${term}%`],
      ),
      nodes: rows<Hit>("select id, name from ElixirNode where name like ? or aliases like ? order by name", [like, like]),
    };
  }, [term]);
  if (!hits) {
    return <Empty>Type at least two letters to search groups, projects, people and Nodes.</Empty>;
  }
  const total = hits.initiatives.length + hits.people.length + hits.nodes.length;
  return (
    <div className="search-results">
      <h1 className="page-title">Results for “{term}”</h1>
      {total === 0 ? <Empty>Nothing matches “{term}”. Try a shorter word, an acronym or a surname.</Empty> : null}
      {hits.nodes.length ? (
        <Section title="Nodes">
          <ul className="hits">
            {hits.nodes.map((hit) => (
              <li key={hit.id}>
                <a href={href("node", hit.id)}>{hit.name}</a>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
      {hits.initiatives.length ? (
        <Section title="Groups and projects">
          <ul className="hits">
            {hits.initiatives.map((hit) => (
              <li key={hit.id}>
                <a href={href("initiative", hit.id)}>{hit.name}</a>
                <span className="kind">{label(hit.kind)}</span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
      {hits.people.length ? (
        <Section title="People">
          <ul className="hits">
            {hits.people.map((hit) => (
              <li key={hit.id}>
                <a href={href("person", hit.id)}>{hit.name}</a>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
    </div>
  );
}

type Listed = { id: string; name: string; people: number; nodes: number; plan: number; start: string | null; end: string | null };

export function KindList({ kind }: { kind: string }) {
  const items = useMemo(
    () =>
      rows<Listed>(
        `select i.id, i.name, i.start, i."end",
           (select count(distinct source) from HoldsRole where target = i.id) people,
           (select count(distinct source) from TakesPartIn where target = i.id) nodes,
           (select count(*) from PlanItemOf where target = i.id) plan
         from Initiative i where i.kind = ? order by i.name`,
        [kind],
      ),
    [kind],
  );
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
