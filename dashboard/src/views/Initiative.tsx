import { useMemo, useState } from "react";
import { Empty, Facts, More, Section, SourceLink } from "../components";
import { list, one, rows, type Row } from "../db";
import { euros, label, period, text } from "../format";
import { href } from "../route";
import { Timeline } from "../Timeline";
import { ReviewList } from "./Reviews";

const LEAD_ORDER = ["lead", "co_lead", "chair", "coordinator", "work_package_lead", "task_lead", "deputy", "liaison", "contact"];

type Role = { person: string; name: string; role_kind: string; role: string; work_item: string | null; funding: string; source_url: string; retrieved_at: string };

function rank(kind: string): number {
  const index = LEAD_ORDER.indexOf(kind);
  return index < 0 ? LEAD_ORDER.length : index;
}

export function InitiativePage({ id }: { id: string }) {
  const data = useMemo(() => {
    const initiative = one("select * from Initiative where id = ?", [id]);
    if (!initiative) {
      return null;
    }
    const plan = rows("select p.* from PlanItemOf o join PlanItem p on p.id = o.source where o.target = ? order by p.date is null, p.date, p.code, p.label", [id]);
    const leads = rows<{ plan: string; id: string; name: string }>(
      "select l.target plan, pe.id, pe.name from LeadsPlanItem l join Person pe on pe.id = l.source join PlanItemOf o on o.source = l.target where o.target = ? group by l.target, pe.id",
      [id],
    );
    const delivered = rows<{ plan: string; id: string; title: string; url: string }>(
      "select d.target plan, o.id, o.title, o.url from Delivers d join Output o on o.id = d.source join PlanItemOf p on p.source = d.target where p.target = ?",
      [id],
    );
    return {
      initiative,
      roles: rows<Role>(
        "select h.source person, p.name, h.role_kind, h.role, h.work_item, h.funding, h.source_url, h.retrieved_at from HoldsRole h join Person p on p.id = h.source where h.target = ?",
        [id],
      ),
      nodes: rows<{ id: string; name: string; sources: number }>(
        "select n.id, n.name, count(distinct t.source_url) sources from TakesPartIn t join ElixirNode n on n.id = t.source where t.target = ? group by n.id order by n.name",
        [id],
      ),
      plan,
      leads,
      delivered,
      outputs: rows("select o.*, f.basis from OutputOf f join Output o on o.id = f.source where f.target = ? order by o.date desc", [id]),
      related: rows<{ id: string; name: string; kind: string; n: number }>(
        `select i.id, i.name, i.kind, count(*) n from RelatedTo r join Initiative i on i.id = case when r.source = ? then r.target else r.source end
         where (r.source = ? or r.target = ?) and i.id != ? group by i.id order by n desc, i.name`,
        [id, id, id, id],
      ),
      statements: rows("select s.* from StatementAbout a join SourceStatement s on s.id = a.source where a.target = ? order by s.coverage, s.source_url", [id]),
      topics: rows<{ label: string }>("select t.label from InitiativeTopic it join Topic t on t.id = it.target where it.source = ? group by t.id order by count(*) desc, t.label", [id]),
      tools: rows("select t.id, t.name, t.url from ToolFor f join Tool t on t.id = f.source where f.target = ? group by t.id order by t.name", [id]),
      events: rows("select e.id, e.title, e.url, e.start from EventFor f join TrainingEvent e on e.id = f.source where f.target = ? group by e.id order by e.start desc", [id]),
      materials: rows("select m.id, m.title, m.url, m.date_published from MaterialFor f join TrainingMaterial m on m.id = f.source where f.target = ? group by m.id order by m.date_published desc", [id]),
      reviews: rows("select * from ReviewItem where status = 'open' and subjects like ?", [`%"${id}"%`]),
    };
  }, [id]);

  if (!data) {
    return <Empty>No group or project has the id “{id}”. Search for it by name instead.</Empty>;
  }
  const { initiative } = data;
  const pages = list(initiative.pages);
  const aliases = list(initiative.aliases).filter((alias) => alias !== initiative.name);
  return (
    <article className={`entity family-${text(initiative.family)}`}>
      <header className="entity-head">
        <p className="kind">{label(initiative.kind)}</p>
        <h1>{text(initiative.name)}</h1>
        {initiative.summary ? <p className="summary">{text(initiative.summary)}</p> : null}
      </header>
      <div className="entity-body">
        <aside className="side">
          <Facts
            facts={[
              ["Acronym", text(initiative.acronym)],
              ["Period", period(initiative.start, initiative.end)],
              ["Status", label(initiative.status)],
              ["EU grant", text(initiative.grant_id)],
              ["EU contribution", euros(initiative.eu_contribution_eur)],
              ["Total cost", euros(initiative.total_cost_eur)],
              ["Nodes taking part", data.nodes.length ? String(data.nodes.length) : ""],
              ["People with a role", String(new Set(data.roles.map((role) => role.person)).size)],
            ]}
          />
          {data.nodes.length ? (
            <div className="side-block">
              <h2>Nodes</h2>
              <ul className="plain">
                {data.nodes.map((node) => (
                  <li key={node.id}>
                    <a href={href("node", node.id)}>{node.name}</a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {pages.length ? (
            <div className="side-block">
              <h2>Pages</h2>
              <ul className="plain">
                {pages.map((page) => (
                  <li key={page}>
                    <SourceLink url={page} full />
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {data.topics.length ? (
            <div className="side-block">
              <h2>EDAM topics</h2>
              <p className="topics">{data.topics.map((topic) => topic.label).join(", ")}</p>
            </div>
          ) : null}
          {aliases.length ? (
            <div className="side-block">
              <h2>Also called</h2>
              <ul className="plain small">
                {aliases.map((alias) => (
                  <li key={alias}>{alias}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {list(initiative.contacts).length ? (
            <div className="side-block">
              <h2>Contacts</h2>
              <ul className="plain small">
                {list(initiative.contacts).map((contact) => (
                  <li key={contact}>
                    {contact.startsWith("http") ? <SourceLink url={contact} full /> : contact.replace(/^mailto:/, "")}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>
        <div className="main">
          {data.reviews.length ? (
            <Section title="Open questions" note={`${data.reviews.length} places where the sources disagree or a match is unclear. A reviewer can settle them in the review decisions file.`}>
              <More items={data.reviews} limit={2} render={(shown) => <ReviewList items={shown} />} />
            </Section>
          ) : null}
          <People roles={data.roles} />
          {data.plan.length ? (
            <Section title="Plan" note={`${data.plan.length} work packages, tasks, deliverables, milestones, goals and other items.`}>
              <Timeline items={data.plan} start={initiative.start} end={initiative.end} />
              <PlanTable plan={data.plan} leads={data.leads} delivered={data.delivered} />
            </Section>
          ) : null}
          {data.outputs.length ? (
            <Section title="Outputs" note="Zenodo records and F1000 items linked to it. 'Named' links rest only on a name in the title or keywords.">
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
                        <span className="basis">{text(output.basis)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              />
            </Section>
          ) : null}
          {data.related.length ? (
            <Section title="Related groups and projects" note="Pages that name both. The kind of link is not recorded.">
              <ul className="hits">
                {data.related.map((item) => (
                  <li key={item.id}>
                    <a href={href("initiative", item.id)}>{item.name}</a>
                    <span className="kind">{label(item.kind)}</span>
                  </li>
                ))}
              </ul>
            </Section>
          ) : null}
          {data.tools.length || data.events.length || data.materials.length ? (
            <Section title="Tools and training" note="bio.tools entries tagged with it, and TeSS events and materials in its collection.">
              <div className="triple">
                <Catalogue title="Tools" items={data.tools} name="name" />
                <Catalogue title="Training events" items={data.events} name="title" date="start" />
                <Catalogue title="Training materials" items={data.materials} name="title" date="date_published" />
              </div>
            </Section>
          ) : null}
          <Section title="What each source says" note="One statement per page or document. Dates and Nodes here are as each source wrote them.">
            <Statements statements={data.statements} />
          </Section>
        </div>
      </div>
    </article>
  );
}

function People({ roles }: { roles: Role[] }) {
  const people = useMemo(() => {
    const byPerson = new Map<string, Role[]>();
    for (const role of roles) {
      byPerson.set(role.person, [...(byPerson.get(role.person) ?? []), role]);
    }
    return [...byPerson.values()]
      .map((held) => held.sort((left, right) => rank(left.role_kind) - rank(right.role_kind)))
      .sort((left, right) => rank(left[0].role_kind) - rank(right[0].role_kind) || left[0].name.localeCompare(right[0].name));
  }, [roles]);
  if (!people.length) {
    return (
      <Section title="People">
        <Empty>No source names anyone in a role here.</Empty>
      </Section>
    );
  }
  return (
    <Section title="People" note={`${people.length} people. Leads first. Funding is 'not stated' unless a source says it.`}>
      <More
        items={people}
        limit={25}
        render={(shown) => (
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Person</th>
                <th scope="col">Role</th>
                <th scope="col">In</th>
                <th scope="col">Source</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((held) => {
                const kinds = [...new Set(held.map((role) => label(role.role_kind)))];
                const items = [...new Set(held.map((role) => role.work_item).filter(Boolean))];
                const sources = [...new Map(held.map((role) => [role.source_url, role])).values()];
                return (
                  <tr key={held[0].person}>
                    <td>
                      <a href={href("person", held[0].person)}>{held[0].name}</a>
                    </td>
                    <td>{kinds.join(", ")}</td>
                    <td className="muted">{items.join("; ")}</td>
                    <td>
                      {sources.slice(0, 3).map((role) => (
                        <SourceLink key={role.source_url} url={role.source_url} retrieved={role.retrieved_at} />
                      ))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      />
    </Section>
  );
}

function PlanTable({ plan, leads, delivered }: { plan: Row[]; leads: { plan: string; id: string; name: string }[]; delivered: { plan: string; id: string; title: string; url: string }[] }) {
  const kinds = [...new Set(plan.map((item) => text(item.kind)))];
  const [kind, setKind] = useState("");
  const shown = kind ? plan.filter((item) => item.kind === kind) : plan;
  return (
    <>
      <div className="filters" role="group" aria-label="Show plan items of one kind">
        <button type="button" aria-pressed={!kind} onClick={() => setKind("")}>
          All {plan.length}
        </button>
        {kinds.map((value) => (
          <button key={value} type="button" aria-pressed={kind === value} onClick={() => setKind(value)}>
            {label(value)} {plan.filter((item) => item.kind === value).length}
          </button>
        ))}
      </div>
      <More
        items={shown}
        limit={30}
        render={(items) => (
          <table className="table plan">
            <thead>
              <tr>
                <th scope="col">Item</th>
                <th scope="col">Date</th>
                <th scope="col">Status</th>
                <th scope="col">Led by</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const by = leads.filter((lead) => lead.plan === item.id);
                const outputs = delivered.filter((output) => output.plan === item.id);
                return (
                  <tr key={text(item.id)}>
                    <td>
                      {item.code ? <span className="code">{text(item.code)}</span> : null} {text(item.label)}
                      {outputs.map((output) => (
                        <a key={output.id} className="delivered" href={output.url} target="_blank" rel="noreferrer">
                          Published as {output.title}
                        </a>
                      ))}
                    </td>
                    <td className="nowrap">{text(item.date) || text(item.date_as_written)}</td>
                    <td>{label(item.status)}</td>
                    <td>
                      {by.length
                        ? by.map((lead, index) => (
                            <span key={lead.id}>
                              {index ? ", " : ""}
                              <a href={href("person", lead.id)}>{lead.name}</a>
                            </span>
                          ))
                        : list(item.leads).join(", ")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      />
    </>
  );
}

function Catalogue({ title, items, name, date }: { title: string; items: Row[]; name: string; date?: string }) {
  return (
    <div>
      <h3>
        {title} <span className="count">{items.length}</span>
      </h3>
      {items.length ? (
        <More
          items={items}
          limit={8}
          render={(shown) => (
            <ul className="plain small">
              {shown.map((item) => (
                <li key={text(item.id)}>
                  <a href={text(item.url)} target="_blank" rel="noreferrer">
                    {text(item[name])}
                  </a>
                  {date && item[date] ? <span className="dates">{text(item[date]).slice(0, 10)}</span> : null}
                </li>
              ))}
            </ul>
          )}
        />
      ) : (
        <p className="empty">None linked.</p>
      )}
    </div>
  );
}

function Statements({ statements }: { statements: Row[] }) {
  if (!statements.length) {
    return <Empty>Only role statements or plan items name it; no page describes it.</Empty>;
  }
  return (
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Source</th>
          <th scope="col">Name there</th>
          <th scope="col">Period</th>
          <th scope="col">Nodes</th>
        </tr>
      </thead>
      <tbody>
        {statements.map((statement) => (
          <tr key={text(statement.id)}>
            <td className="source-cell">
              <SourceLink url={statement.source_url} retrieved={statement.retrieved_at} full />
              <span className="muted block">{statement.coverage === "described" ? "Describes it" : "Lists it"}</span>
            </td>
            <td>{text(statement.name_as_written)}</td>
            <td className="nowrap">{period(statement.start, statement.end) || text(statement.period)}</td>
            <td className="muted">{list(statement.nodes).join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

