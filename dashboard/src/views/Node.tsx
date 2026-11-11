import { useMemo } from "react";
import { Empty, Facts, More, Section } from "../components";
import { list, one, rows } from "../db";
import { count, label, text } from "../format";
import { href } from "../route";

type Taking = { id: string; name: string; kind: string; family: string; start: string | null; end: string | null };
type Member = { id: string; name: string; places: number; leads: number };

export function NodePage({ id }: { id: string }) {
  const data = useMemo(() => {
    const node = one("select * from ElixirNode where id = ?", [id]);
    if (!node) {
      return null;
    }
    return {
      node,
      initiatives: rows<Taking>(
        `select i.id, i.name, i.kind, i.family, i.start, i."end" from TakesPartIn t join Initiative i on i.id = t.target
         where t.source = ? group by i.id order by i.family, i.kind, i.name`,
        [id],
      ),
      people: rows<Member>(
        `select p.id, p.name,
           (select count(distinct target) from HoldsRole where source = p.id) places,
           (select count(distinct target) from HoldsRole where source = p.id and role_kind in ('lead', 'co_lead', 'chair', 'coordinator', 'work_package_lead', 'task_lead')) leads
         from InNode n join Person p on p.id = n.source where n.target = ? group by p.id order by leads desc, places desc, p.name`,
        [id],
      ),
      tools: one<{ n: number }>("select count(distinct source) n from ToolInNode where target = ?", [id])?.n ?? 0,
      events: one<{ n: number }>("select count(distinct source) n from EventInNode where target = ?", [id])?.n ?? 0,
      materials: one<{ n: number }>("select count(distinct source) n from MaterialInNode where target = ?", [id])?.n ?? 0,
    };
  }, [id]);
  if (!data) {
    return <Empty>No Node has the id “{id}”.</Empty>;
  }
  const { node } = data;
  const groups = data.initiatives.filter((item) => item.family === "group");
  const projects = data.initiatives.filter((item) => item.family === "project");
  return (
    <article className="entity family-node">
      <header className="entity-head">
        <p className="kind">{label(node.kind)}</p>
        <h1>{text(node.name)}</h1>
        <p className="summary">
          Takes part in {count(groups.length, "group", "groups")} and {count(projects.length, "project", "projects")}. Sources place {count(data.people.length, "person", "people")} in this Node.
        </p>
      </header>
      <div className="entity-body">
        <aside className="side">
          <Facts
            facts={[
              ["Country", text(node.country)],
              ["bio.tools entries", data.tools.toLocaleString("en")],
              ["TeSS events", data.events.toLocaleString("en")],
              ["TeSS materials", data.materials.toLocaleString("en")],
              ["Also written", list(node.aliases).join("; ")],
            ]}
          />
        </aside>
        <div className="main">
          <Section title="Groups" note="Groups a source names this Node in.">
            <Taken items={groups} />
          </Section>
          <Section title="Projects" note="Projects a source names this Node in, including work-package and CORDIS participation.">
            <Taken items={projects} />
          </Section>
          <Section title="People" note="People that a source places in this Node, with the number of groups and projects they hold a role in.">
            {data.people.length ? (
              <More
                items={data.people}
                limit={30}
                render={(shown) => (
                  <table className="table">
                    <thead>
                      <tr>
                        <th scope="col">Person</th>
                        <th scope="col" className="number">Leading roles</th>
                        <th scope="col" className="number">Groups and projects</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shown.map((person) => (
                        <tr key={person.id}>
                          <td>
                            <a href={href("person", person.id)}>{person.name}</a>
                          </td>
                          <td className="number">{person.leads || ""}</td>
                          <td className="number">{person.places || ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              />
            ) : (
              <Empty>No source places anyone in this Node.</Empty>
            )}
          </Section>
        </div>
      </div>
    </article>
  );
}

function Taken({ items }: { items: Taking[] }) {
  if (!items.length) {
    return <Empty>None recorded.</Empty>;
  }
  return (
    <More
      items={items}
      limit={30}
      render={(shown) => (
        <ul className="hits">
          {shown.map((item) => (
            <li key={item.id}>
              <a href={href("initiative", item.id)}>{item.name}</a>
              <span className="kind">{label(item.kind)}</span>
            </li>
          ))}
        </ul>
      )}
    />
  );
}
