import { Fragment, useMemo, useRef, useState } from "react";
import { RequestState, Section, SourceLink } from "../components";
import { apiUrl, list, type Value, useApi } from "../db";
import { label, text } from "../format";
import { href } from "../route";

type Project = {
  id: string;
  name: string;
  kind: string;
  family: string;
  start: Value;
  end: Value;
  period: Value;
  period_status: Value;
  bases: Value;
  beneficiaries: Value;
  sources: Value;
  limits: Value;
};
type Commitment = {
  initiative: string;
  id: string;
  code: Value;
  kind: string;
  label: string;
  date: Value;
  status: Value;
  role: Value;
  person: string;
  person_name: string;
  source_url: Value;
};
type Output = { id: string; title: string; date: Value; url: Value; resource_type: Value; kind: Value; authors: Value; projects: Value; project_ids: Value };
type Period = "running" | "ended" | "all";
type Filter = { period: Period; since: string; kinds: string[] };
type Data = {
  node: { id: string; name: string };
  nodes: { id: string; name: string }[];
  projects: Project[];
  commitments: Commitment[];
  years: string[];
  year: string;
  outputs: Output[];
};

const TONES: Record<string, string> = {
  eu_project: "a",
  commissioned_service: "c",
  implementation_study: "g",
  staff_exchange: "t",
};

const BASES: Record<string, string> = {
  own_page: "the project's own page lists the Node",
  people: "Node people hold roles in it",
  beneficiary: "a Node organisation is an EU beneficiary",
  work_package: "named in a work package",
};

function names(value: Value): string {
  return text(value).split(",").map((n) => n.trim()).filter(Boolean).join(", ");
}

export function PortfolioPage({ id }: { id: string }) {
  const [year, setYear] = useState("");
  const [node, query] = id.split("?");
  if (!node) return <NodeChooser />;
  return <Portfolio key={node} id={node} query={new URLSearchParams(query ?? "")} year={year} onYear={setYear} />;
}

function readFilter(query: URLSearchParams): Filter | null {
  const period = query.get("period");
  if (!period) return null;
  return {
    period: (["running", "ended", "all"].includes(period) ? period : "all") as Period,
    since: /^\d{4}$/.test(query.get("since") ?? "") ? query.get("since")! : "",
    kinds: (query.get("kinds") ?? "").split(",").filter((k) => k in TONES),
  };
}

function writeFilter(node: string, filter: Filter) {
  const query = new URLSearchParams({ period: filter.period });
  if (filter.since) query.set("since", filter.since);
  if (filter.kinds.length) query.set("kinds", filter.kinds.join(","));
  window.history.replaceState(null, "", `#/portfolio/${encodeURIComponent(node)}?${query}`);
}

function matches(p: Project, filter: Filter): boolean {
  if (filter.period === "running" && p.period_status !== "running") return false;
  if (filter.period === "ended" && p.period_status === "running") return false;
  if (filter.since && text(p.end) && text(p.end).slice(0, 4) < filter.since) return false;
  if (filter.kinds.length && !filter.kinds.includes(TONES[p.kind] ? p.kind : "other")) return false;
  return true;
}

function NodeChooser() {
  const { data, error } = useApi<{ nodes: { id: string; name: string; initiatives: number; people: number }[] }>(apiUrl("home"));
  if (!data) return <RequestState error={error} />;
  return (
    <>
      <section className="hero">
        <h1>What has your Node taken part in?</h1>
        <p className="lede">Choose a Node to see its projects over time, what its people committed to, who works on what, and its outputs for the annual report.</p>
      </section>
      <ul className="portfolio-nodes">
        {[...data.nodes].sort((a, b) => a.name.localeCompare(b.name)).map((n) => (
          <li key={n.id}>
            <a href={href("portfolio", n.id)}>{n.name}</a>
            <small>{n.initiatives} groups and projects</small>
          </li>
        ))}
      </ul>
    </>
  );
}

function Portfolio({ id, query, year, onYear }: { id: string; query: URLSearchParams; year: string; onYear: (y: string) => void }) {
  const { data: fresh, error } = useApi<Data>(apiUrl("portfolio", { id, year }));
  const last = useRef<Data | undefined>(undefined);
  if (fresh) last.current = fresh;
  const data = fresh ?? last.current;
  const loading = !fresh && !!data;
  const [open, setOpen] = useState<string | null>(null);
  const [chosen, setChosen] = useState<Filter | null>(() => readFilter(query));
  const byProject = useMemo(() => {
    const out = new Map<string, Commitment[]>();
    for (const c of data?.commitments ?? []) out.set(c.initiative, [...(out.get(c.initiative) ?? []), c]);
    return out;
  }, [data]);
  if (!data) return <RequestState error={error} />;
  const all = data.projects
    .filter((p) => p.family === "project")
    .sort((a, b) => Number(b.period_status === "running") - Number(a.period_status === "running") || text(b.start).localeCompare(text(a.start)) || a.name.localeCompare(b.name));
  const groups = data.projects.filter((p) => p.family !== "project");
  const runningAll = all.filter((p) => p.period_status === "running").length;
  const filter: Filter = chosen ?? { period: runningAll ? "running" : "all", since: "", kinds: [] };
  const setFilter = (next: Filter) => {
    setChosen(next);
    writeFilter(id, next);
  };
  const projects = all.filter((p) => matches(p, filter));
  const shown = new Set(projects.map((p) => p.id));
  const commitments = data.commitments.filter((c) => shown.has(c.initiative));
  const running = projects.filter((p) => p.period_status === "running").length;
  const people = new Set(commitments.map((c) => c.person)).size;
  const items = new Set(commitments.map((c) => c.id)).size;
  const narrowed = projects.length < all.length;
  const outputs = narrowed
    ? data.outputs.filter((o) => text(o.project_ids).split(",").some((p) => shown.has(p.trim())))
    : data.outputs;
  const unlinked = narrowed ? data.outputs.filter((o) => !text(o.project_ids)) : [];
  const limits = text(data.projects.find((p) => p.limits)?.limits);
  return (
    <>
      <section className="hero portfolio-hero">
        <label className="portfolio-switch">
          <span className="visually-hidden">Node</span>
          <select value={id} onChange={(e) => (window.location.hash = href("portfolio", e.target.value))}>
            {data.nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.name}
              </option>
            ))}
          </select>
        </label>
        <h1>{data.node.name}'s portfolio</h1>
        <p className="lede">
          Sources place {data.node.name} in {all.length} projects, {runningAll} of them running now, and in {groups.length} groups.
        </p>
      </section>
      <FilterBar filter={filter} onChange={setFilter} all={all} />
      <p className="portfolio-showing" role="status">
        {narrowed ? `Showing ${projects.length} of ${all.length} projects` : `Showing all ${all.length} projects`}
        {!projects.length ? "." : items ? `, with ${people} ${people === 1 ? "person" : "people"} from the Node named on ${items} plan ${items === 1 ? "item" : "items"}.` : "; no plan item in them names the Node's people."}
        {running && filter.period !== "running" ? ` ${running} running.` : ""}
      </p>
      {!projects.length ? (
        <p className="empty">
          No project matches.{" "}
          <button type="button" className="portfolio-reset" onClick={() => setFilter({ period: "all", since: "", kinds: [] })}>
            Show all {all.length} projects
          </button>
        </p>
      ) : null}
      {projects.length ? (
        <>
      <Section title="Projects over time" note="Each bar runs from a project's start to its end; projects without dates are listed below the chart.">
        <Timeline projects={projects} />
      </Section>
      <Section title="Projects and what we committed to" note="Open a project to see the plan items the Node's people are named on.">
        <table className="table portfolio-projects">
          <thead>
            <tr>
              <th scope="col">Project</th>
              <th scope="col">Period</th>
              <th scope="col">EU funding to Node organisations</th>
              <th scope="col" className="number">
                Plan items
              </th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => {
              const mine = byProject.get(p.id) ?? [];
              const isOpen = open === p.id;
              return (
                <Fragment key={p.id}>
                  <tr>
                    <td>
                      <button type="button" className="portfolio-toggle" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : p.id)} disabled={!mine.length}>
                        <span className={`portfolio-swatch tone-${TONES[p.kind] ?? "ink"}`} aria-hidden="true" />
                        {p.name}
                      </button>
                      <small className="portfolio-why" title={list(p.bases).map((b) => BASES[b] ?? label(b)).join("; ")}>
                        {label(p.kind)}
                        {p.period_status === "running" ? ", running" : ""}
                      </small>
                    </td>
                    <td className="portfolio-period">{text(p.period)}</td>
                    <td>{list(p.beneficiaries).length ? list(p.beneficiaries).join("; ") : <span className="muted">Not stated</span>}</td>
                    <td className="number">{new Set(mine.map((c) => c.id)).size || ""}</td>
                  </tr>
                  {isOpen ? (
                    <tr className="portfolio-detail">
                      <td colSpan={4}>
                        <Commitments items={mine} />
                        <p className="note">
                          <a href={href("initiative", p.id)}>Open the full project record</a>
                          {list(p.sources).length ? <> or its source <SourceLink url={list(p.sources)[0]} /></> : null}
                        </p>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </Section>
        </>
      ) : null}
      <Section title="Who works on what" note="People a source places in this Node, with the plan items they are named on.">
        <People commitments={commitments} projects={data.projects} />
      </Section>
      <Section
        title="Outputs for the annual report"
        note={narrowed ? "Outputs with at least one author placed in this Node, from the projects shown." : "Outputs with at least one author a source places in this Node."}
      >
        {data.years.length ? (
          <>
            <div className="filters" role="group" aria-label="Year" aria-busy={loading}>
              {data.years.slice(0, 8).map((y) => (
                <button key={y} type="button" aria-pressed={y === data.year} onClick={() => onYear(y)}>
                  {y}
                </button>
              ))}
              {loading ? <span className="note">Loading {year}…</span> : null}
            </div>
            {outputs.length ? (
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Output</th>
                    <th scope="col">Date</th>
                    <th scope="col">Node authors</th>
                    <th scope="col">Project</th>
                  </tr>
                </thead>
                <tbody>
                  {outputs.map((o) => (
                    <tr key={o.id}>
                      <td>
                        <a href={text(o.url)} target="_blank" rel="noreferrer">
                          {o.title}
                        </a>
                        {o.resource_type ? <small className="portfolio-why">{text(o.resource_type)}</small> : null}
                      </td>
                      <td>{text(o.date).slice(0, 10)}</td>
                      <td>{names(o.authors)}</td>
                      <td>{names(o.projects) || <span className="muted">None linked</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="empty">No output from {year || data.year} {narrowed ? "in the projects shown " : ""}has an author placed in this Node.</p>
            )}
            {unlinked.length ? (
              <details className="portfolio-unlinked">
                <summary>
                  {unlinked.length} more {unlinked.length === 1 ? "output is" : "outputs are"} not linked to any project
                </summary>
                <ul className="portfolio-people">
                  {unlinked.map((o) => (
                    <li key={o.id}>
                      <a href={text(o.url)} target="_blank" rel="noreferrer">
                        {o.title}
                      </a>
                      <small>
                        {text(o.date).slice(0, 10)}, {names(o.authors)}
                      </small>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </>
        ) : (
          <p className="empty">No output in the atlas has an author placed in this Node.</p>
        )}
      </Section>
      {limits ? <p className="note portfolio-limits">{limits} Authors missing an affiliation are not counted here.</p> : null}
    </>
  );
}

function Commitments({ items }: { items: Commitment[] }) {
  if (!items.length) return <p className="empty">No plan item names the Node's people.</p>;
  const sorted = [...items].sort((a, b) => text(a.code).localeCompare(text(b.code), undefined, { numeric: true }) || a.person_name.localeCompare(b.person_name));
  return (
    <table className="table portfolio-commitments">
      <thead>
        <tr>
          <th scope="col">Plan item</th>
          <th scope="col">Due</th>
          <th scope="col">Status</th>
          <th scope="col">Who</th>
          <th scope="col">Source</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((c) => (
          <tr key={`${c.id}-${c.person}-${text(c.role)}`}>
            <td>
              <a href={href("record", `PlanItem/${c.id}`)}>
                {text(c.code) ? `${text(c.code)}: ` : ""}
                {c.label}
              </a>
              <small className="portfolio-why">{label(c.kind)}</small>
            </td>
            <td className="portfolio-period">{text(c.date) || <span className="muted">Not stated</span>}</td>
            <td>{label(text(c.status))}</td>
            <td>
              <a href={href("person", c.person)}>{c.person_name}</a>
              {text(c.role) === "lead" ? <small className="portfolio-why">Lead</small> : null}
            </td>
            <td>
              <SourceLink url={c.source_url} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function People({ commitments, projects }: { commitments: Commitment[]; projects: Project[] }) {
  const projectName = new Map(projects.map((p) => [p.id, p.name]));
  const people = new Map<string, { name: string; items: Commitment[] }>();
  for (const c of commitments) {
    const entry = people.get(c.person) ?? { name: c.person_name, items: [] };
    if (!entry.items.some((x) => x.id === c.id)) entry.items.push(c);
    people.set(c.person, entry);
  }
  if (!people.size) return <p className="empty">No plan item names a person placed in this Node.</p>;
  return (
    <ul className="portfolio-people">
      {[...people.entries()]
        .sort((a, b) => b[1].items.length - a[1].items.length || a[1].name.localeCompare(b[1].name))
        .map(([pid, p]) => (
          <li key={pid}>
            <a href={href("person", pid)}>{p.name}</a>
            <ul>
              {p.items.map((c) => (
                <li key={c.id}>
                  {text(c.code) ? `${text(c.code)}: ` : ""}
                  {c.label}
                  <small>
                    {projectName.get(c.initiative) ?? c.initiative}
                    {text(c.role) === "lead" ? ", lead" : ""}
                  </small>
                </li>
              ))}
            </ul>
          </li>
        ))}
    </ul>
  );
}

function yearOf(value: Value): number | null {
  const match = /^(\d{4})(?:-(\d{2}))?/.exec(text(value));
  return match ? Number(match[1]) + (match[2] ? (Number(match[2]) - 1) / 12 : 0) : null;
}

function Timeline({ projects }: { projects: Project[] }) {
  const now = new Date().getFullYear() + new Date().getMonth() / 12;
  const dated = projects
    .map((p) => ({ p, from: yearOf(p.start), to: yearOf(p.end) }))
    .filter((x): x is { p: Project; from: number; to: number | null } => x.from !== null)
    .sort((a, b) => a.from - b.from || a.p.name.localeCompare(b.p.name));
  const undated = projects.filter((p) => yearOf(p.start) === null);
  if (!dated.length) return <p className="empty">No project of this Node has dates.</p>;
  const first = Math.floor(Math.min(...dated.map((d) => d.from)));
  const last = Math.ceil(Math.max(now, ...dated.map((d) => d.to ?? now))) + 0.001;
  const at = (v: number) => `${((v - first) / (last - first)) * 100}%`;
  const ticks = Array.from({ length: Math.floor(last) - first + 1 }, (_, i) => first + i);
  const step = ticks.length > 12 ? 2 : 1;
  return (
    <figure className="portfolio-timeline">
      <div className="portfolio-axis" aria-hidden="true">
        {ticks.filter((t) => (t - first) % step === 0).map((t) => (
          <span key={t} style={{ left: at(t), transform: t === first ? "none" : t >= Math.floor(last) ? "translateX(-100%)" : undefined }}>
            {t}
          </span>
        ))}
        <span className="portfolio-today" style={{ left: at(now) }} />
      </div>
      <ol>
        {dated.map(({ p, from, to }) => {
          const end = to ?? now;
          return (
            <li key={p.id} className={`tone-${TONES[p.kind] ?? "ink"}${to === null ? " open-ended" : ""}`}>
              <a href={href("initiative", p.id)} style={{ marginLeft: at(from), width: `max(6px, calc(${at(end)} - ${at(from)}))` }} title={`${p.name}, ${text(p.period)}`}>
                <span className="visually-hidden">
                  {p.name}, {text(p.period)}
                </span>
              </a>
              <span
                className="portfolio-label"
                style={(from - first) / (last - first) > 0.55 ? { right: `calc(100% - ${at(end)})`, left: "auto", textAlign: "right" } : { left: at(from), maxWidth: `calc(100% - ${at(from)})` }}
                aria-hidden="true"
              >
                {p.name}
              </span>
            </li>
          );
        })}
      </ol>
      <figcaption>The dashed line is today; the colours match the kinds in the filter above.</figcaption>
      {undated.length ? <p className="note">Without dates: {undated.map((p) => p.name).join(", ")}.</p> : null}
    </figure>
  );
}

function FilterBar({ filter, onChange, all }: { filter: Filter; onChange: (f: Filter) => void; all: Project[] }) {
  const ends = [...new Set(all.map((p) => text(p.end).slice(0, 4)).filter(Boolean))].sort().reverse();
  const kinds = [...Object.keys(TONES), "other"].filter((k) => all.some((p) => (TONES[p.kind] ? p.kind : "other") === k));
  const toggle = (kind: string) =>
    onChange({ ...filter, kinds: filter.kinds.includes(kind) ? filter.kinds.filter((k) => k !== kind) : [...filter.kinds, kind] });
  const periods: [Period, string][] = [
    ["running", "Running now"],
    ["ended", "Ended"],
    ["all", "All"],
  ];
  return (
    <div className="portfolio-filters">
      <div role="group" aria-label="Period" className="portfolio-segment">
        {periods.map(([value, name]) => (
          <button key={value} type="button" aria-pressed={filter.period === value} onClick={() => onChange({ ...filter, period: value, since: value === "running" ? "" : filter.since })}>
            {name}
          </button>
        ))}
      </div>
      {filter.period !== "running" ? (
        <label className="portfolio-since">
          Ended in or after{" "}
          <select value={filter.since} onChange={(e) => onChange({ ...filter, since: e.target.value })}>
            <option value="">any year</option>
            {ends.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <div role="group" aria-label="Kind of project" className="portfolio-kinds">
        {kinds.map((kind) => (
          <button key={kind} type="button" aria-pressed={filter.kinds.includes(kind)} onClick={() => toggle(kind)}>
            <span className={`portfolio-swatch tone-${TONES[kind] ?? "ink"}`} aria-hidden="true" />
            {kind === "other" ? "Other" : label(kind)}
          </button>
        ))}
      </div>
    </div>
  );
}
