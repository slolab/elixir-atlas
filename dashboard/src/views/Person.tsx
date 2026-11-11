import { useMemo } from "react";
import { Empty, Facts, More, Section, SourceLink } from "../components";
import { list, one, rows } from "../db";
import { label, text } from "../format";
import { href } from "../route";
import { ReviewList } from "./Reviews";

export function PersonPage({ id }: { id: string }) {
  const data = useMemo(() => {
    const person = one("select * from Person where id = ?", [id]);
    if (!person) {
      return null;
    }
    return {
      person,
      nodes: rows<{ id: string; name: string }>("select n.id, n.name from InNode i join ElixirNode n on n.id = i.target where i.source = ? group by n.id order by n.name", [id]),
      roles: rows(
        `select h.*, i.name initiative, i.kind from HoldsRole h join Initiative i on i.id = h.target where h.source = ?
         order by i.family, i.name, h.role_kind`,
        [id],
      ),
      led: rows(
        `select p.id, p.code, p.label, p.kind, p.date, p.status, i.id initiative, i.name initiative_name
         from LeadsPlanItem l join PlanItem p on p.id = l.target join PlanItemOf o on o.source = p.id join Initiative i on i.id = o.target
         where l.source = ? group by p.id order by p.date is null, p.date`,
        [id],
      ),
      outputs: rows("select o.id, o.title, o.url, o.date from Authored a join Output o on o.id = a.target where a.source = ? group by o.id order by o.date desc", [id]),
      tools: rows("select t.id, t.name, t.url from CreditedForTool c join Tool t on t.id = c.target where c.source = ? group by t.id order by t.name", [id]),
      organisations: rows<{ name: string }>("select g.name from AffiliatedWith a join Organisation g on g.id = a.target where a.source = ? group by g.id order by g.name", [id]),
      reviews: rows("select * from ReviewItem where status = 'open' and subjects like ?", [`%"${id}"%`]),
    };
  }, [id]);
  if (!data) {
    return <Empty>No person has the id “{id}”. Search for them by name instead.</Empty>;
  }
  const { person } = data;
  const places = new Set(data.roles.map((role) => role.target)).size;
  const variants = list(person.name_variants).filter((name) => name !== person.name);
  return (
    <article className="entity family-person">
      <header className="entity-head">
        <p className="kind">Person</p>
        <h1>{text(person.name)}</h1>
        <p className="summary">
          {places ? `Holds ${data.roles.length} roles in ${places} groups and projects.` : "No source gives this person a role in a group or project."}
          {data.led.length ? ` Leads ${data.led.length} plan items.` : ""}
        </p>
      </header>
      <div className="entity-body">
        <aside className="side">
          <Facts
            facts={[
              ["Nodes", data.nodes.length ? data.nodes.map((node, index) => (
                <span key={node.id}>
                  {index ? ", " : ""}
                  <a href={href("node", node.id)}>{node.name}</a>
                </span>
              )) : ""],
              ["Organisations", data.organisations.map((organisation) => organisation.name).join("; ")],
              ["ORCID", list(person.orcids).map((orcid) => (
                <a key={orcid} href={`https://orcid.org/${orcid}`} target="_blank" rel="noreferrer">
                  {orcid}
                </a>
              ))],
              ["Email domains", list(person.email_domains).join(", ")],
              ["Known from", list(person.source_kinds).map(label).join(", ")],
              ["Also written", variants.join("; ")],
            ]}
          />
        </aside>
        <div className="main">
          {data.reviews.length ? (
            <Section title="Open questions" note="This record may be the same person as another one. A reviewer can settle it in the review decisions file.">
              <More items={data.reviews} limit={2} render={(shown) => <ReviewList items={shown} />} />
            </Section>
          ) : null}
          <Section title="Roles">
            {data.roles.length ? (
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Group or project</th>
                    <th scope="col">Role</th>
                    <th scope="col">In</th>
                    <th scope="col">Funding</th>
                    <th scope="col">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {data.roles.map((role) => (
                    <tr key={text(role.id)}>
                      <td>
                        <a href={href("initiative", text(role.target))}>{text(role.initiative)}</a>
                        <span className="muted block">{label(role.kind)}</span>
                      </td>
                      <td>
                        {label(role.role_kind)}
                        {role.role && label(role.role) !== label(role.role_kind) ? <span className="muted block">{text(role.role)}</span> : null}
                      </td>
                      <td className="muted">{text(role.work_item)}</td>
                      <td>{label(role.funding)}</td>
                      <td>
                        <SourceLink url={role.source_url} retrieved={role.retrieved_at} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <Empty>No roles recorded.</Empty>
            )}
          </Section>
          {data.led.length ? (
            <Section title="Plan items led">
              <table className="table plan">
                <thead>
                  <tr>
                    <th scope="col">Item</th>
                    <th scope="col">Of</th>
                    <th scope="col">Date</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.led.map((item) => (
                    <tr key={text(item.id)}>
                      <td>
                        {item.code ? <span className="code">{text(item.code)}</span> : null} {text(item.label)}
                      </td>
                      <td>
                        <a href={href("initiative", text(item.initiative))}>{text(item.initiative_name)}</a>
                      </td>
                      <td className="nowrap">{text(item.date)}</td>
                      <td>{label(item.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          ) : null}
          {data.outputs.length ? (
            <Section title="Outputs authored">
              <More
                items={data.outputs}
                limit={12}
                render={(shown) => (
                  <ul className="outputs">
                    {shown.map((output) => (
                      <li key={text(output.id)}>
                        <a href={text(output.url)} target="_blank" rel="noreferrer">
                          {text(output.title)}
                        </a>
                        <span className="dates">{text(output.date)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              />
            </Section>
          ) : null}
          {data.tools.length ? (
            <Section title="Tools credited">
              <ul className="plain">
                {data.tools.map((tool) => (
                  <li key={text(tool.id)}>
                    <a href={text(tool.url)} target="_blank" rel="noreferrer">
                      {text(tool.name)}
                    </a>
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}
        </div>
      </div>
    </article>
  );
}
