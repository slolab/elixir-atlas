import { useMemo } from "react";
import { Chromatogram } from "../Chromatogram";
import { Bars, Section } from "../components";
import { rows } from "../db";
import { label } from "../format";
import { href } from "../route";

export function Home() {
  const data = useMemo(
    () => ({
      kinds: rows<{ kind: string; n: number }>("select kind, count(*) n from Initiative group by kind order by n desc"),
      nodes: rows<{ id: string; name: string; initiatives: number; people: number }>(
        `select n.id, n.name,
          (select count(distinct target) from TakesPartIn where source = n.id) initiatives,
          (select count(distinct source) from InNode where target = n.id) people
         from ElixirNode n order by initiatives desc, n.name`,
      ),
      reviews: rows<{ kind: string; n: number }>("select kind, count(*) n from ReviewItem where status = 'open' group by kind order by n desc"),
    }),
    [],
  );
  return (
    <>
      <section className="hero">
        <h1>Projects running each month</h1>
        <p className="lede">
          Four kinds of ELIXIR project, traced from their start and end dates. Search above for any group, project, person or Node.
        </p>
        <Chromatogram />
      </section>
      <div className="columns">
        <Section title="Groups and projects by kind">
          <Bars bars={data.kinds.map((kind) => ({ key: kind.kind, name: <a href={href("kind", kind.kind)}>{label(kind.kind)}</a>, value: kind.n }))} />
        </Section>
        <Section title="Nodes by number of groups and projects" note="People counts are those the sources place in the Node.">
          <Bars
            tone="c"
            bars={data.nodes.map((node) => ({
              key: node.id,
              name: <a href={href("node", node.id)}>{node.name}</a>,
              value: node.initiatives,
              extra: `${node.people} people`,
            }))}
          />
        </Section>
        <Section title="Open review items" note="Questions the build could not settle from the sources.">
          <Bars
            bars={data.reviews.map((review) => ({
              key: review.kind,
              name: <a href={href("reviews", review.kind)}>{label(review.kind)}</a>,
              value: review.n,
            }))}
          />
        </Section>
      </div>
    </>
  );
}
