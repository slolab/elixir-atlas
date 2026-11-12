import { useId, useMemo, useState, type MouseEvent } from "react";
import { EntityLink, More, RequestState, Section, SourceLink } from "../components";
import { apiUrl, list, type Value, useApi } from "../db";
import { text } from "../format";
import { href, recordHref } from "../route";

type TopicRow = { id: string; label: string; communities: number; tools: number; materials: number };
type Basis = { community: string; basis: string; purpose: Value; evidence: Value; source_url: Value };
type Community = {
  id: string;
  name: string;
  topics: { label: string; evidence: Value; source_url: Value; retrieved_at: Value }[];
  tools: number;
  contacts?: Value;
  join_url?: Value;
  joining?: Value;
  page?: Value;
  leads?: { id: string; name: string; roles: string }[];
};
type Resource = { id: string; name: string; kind: string; url: Value; by: Basis[] };
type Tool = { id: string; name: string; homepage: Value; url: Value; tool_types: Value; listed_for: Value };
type Paper = { id: string; title: string; date: Value; url: Value; community: string };
type Material = { id: string; title: string; url: Value; date_published: Value; content_provider: Value };
type Event = { id: string; title: string; url: Value; start: Value; city: Value; country: Value; online: Value };
type Support = {
  topics: { id: string; label: string }[];
  communities: Community[];
  resources: Resource[];
  tools: Tool[];
  tools_total: number;
  papers: Paper[];
  papers_total: number;
  materials: Material[];
  materials_total: number;
  events: Event[];
  events_total: number;
};

const KINDS: [string, string][] = [
  ["standard", "Standards"],
  ["guideline", "Guidelines"],
  ["practice", "Good practice"],
  ["database", "Databases and registries"],
  ["tool", "Tools"],
  ["training", "Training resources"],
  ["document", "Documents"],
];

export function TopicPage({ id }: { id: string }) {
  const chosen = [...new Set(id.split(",").filter(Boolean))];
  const { data: topics, error } = useApi<TopicRow[]>(apiUrl("topics"));
  if (!topics) return <RequestState error={error} />;
  const go = (ids: string[]) => {
    window.location.hash = ids.length ? href("topic", ids.join(",")) : href("topic");
  };
  return (
    <div className="finder">
      <section className="hero finder-hero">
        <h1>What does ELIXIR offer for your research?</h1>
        <p className="lede">
          Find the Communities working in your area, get in touch, and explore the resources and training connected to their work.
        </p>
        <TopicPicker topics={topics} chosen={chosen} onChange={go} />
      </section>
      {chosen.length ? <Results ids={chosen} /> : <Starters topics={topics} onPick={(t) => go([t])} />}
    </div>
  );
}

function TopicPicker({ topics, chosen, onChange }: { topics: TopicRow[]; chosen: string[]; onChange: (ids: string[]) => void }) {
  const [query, setQuery] = useState("");
  const listId = useId();
  const byId = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics]);
  const words = query.trim().toLowerCase();
  const tokens = words.split(/[\s-]+/).filter((word) => word.length > 2);
  const score = (topic: TopicRow) => tokens.filter((word) => topic.label.toLowerCase().includes(word)).length;
  const matches = words
    ? topics
        .filter((t) => !chosen.includes(t.id) && (t.label.toLowerCase().includes(words) || score(t) > 0))
        .sort((a, b) => score(b) - score(a) || b.communities - a.communities || b.tools - a.tools || a.label.localeCompare(b.label))
        .slice(0, 8)
    : [];
  const add = (topic: string) => {
    onChange([...chosen, topic]);
    setQuery("");
  };
  return (
    <div className="finder-picker">
      <label htmlFor={`${listId}-input`}>
        What is your research about?
      </label>
      <input
        id={`${listId}-input`}
        type="search"
        disabled={chosen.length >= 10}
        autoComplete="off"
        placeholder="Type a research area, for example metabolomics"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && matches[0]) add(matches[0].id);
          if (event.key === "Escape") setQuery("");
        }}
        aria-controls={listId}
        aria-describedby={`${listId}-hint`}
      />
      <p className="note finder-hint" id={`${listId}-hint`}>
        {chosen.length >= 10 ? "Ten areas selected. Remove an area to choose another." : "Choose up to ten areas. Results include matches to any selected area."}
      </p>
      {matches.length ? (
        <ul id={listId} className="finder-suggestions">
          {matches.map((t) => (
            <li key={t.id}>
              <button type="button" onClick={() => add(t.id)}>
                <span>{t.label}</span>
                <small>{coverage(t)}</small>
              </button>
            </li>
          ))}
        </ul>
      ) : words ? (
        <p className="note" role="status">No matching area found. Try a broader term, such as "modelling", "systems biology" or "omics".</p>
      ) : null}
      {chosen.length ? (
        <ul className="finder-chosen" aria-label="Chosen research areas">
          {chosen.map((t) => (
            <li key={t}>
              {byId.get(t)?.label ?? t}
              <button type="button" aria-label={`Remove ${byId.get(t)?.label ?? t}`} onClick={() => onChange(chosen.filter((x) => x !== t))}>
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function coverage(t: TopicRow): string {
  const parts = [
    t.communities ? `${t.communities} ${t.communities === 1 ? "Community" : "Communities"}` : "",
    t.tools ? `${t.tools} tools` : "",
    t.materials ? `${t.materials} training materials` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(", ") : "nothing linked yet";
}

function Starters({ topics, onPick }: { topics: TopicRow[]; onPick: (id: string) => void }) {
  const popular = [...topics].sort((a, b) => Number(b.label === "Systems biology") - Number(a.label === "Systems biology") || b.communities - a.communities || b.tools - a.tools).slice(0, 8);
  return (
    <Section title="Explore a research area" note="Start with Systems biology for metabolic modelling, or choose an area below.">
      <ul className="finder-starters">
        {popular.map((t) => (
          <li key={t.id}>
            <button type="button" onClick={() => onPick(t.id)}>
              {t.label}
              <small>{coverage(t)}</small>
            </button>
          </li>
        ))}
      </ul>
    </Section>
  );
}

function Results({ ids }: { ids: string[] }) {
  const { data, error } = useApi<Support>(apiUrl("topic-support", { topics: ids.join(",") }));
  if (!data) return <RequestState error={error} />;
  const area = data.topics.map((t) => t.label).join(" or ");
  return (
    <>
      <nav className="finder-sections" aria-label="Research support sections">
        <a href="#finder-communities" onClick={(event) => scrollToSection(event, "finder-communities")}>Communities <span>{data.communities.length}</span></a>
        <a href="#finder-resources" onClick={(event) => scrollToSection(event, "finder-resources")}>Resources <span>{data.resources.length}</span></a>
        <a href="#finder-tools" onClick={(event) => scrollToSection(event, "finder-tools")}>Tools <span>{data.tools_total}</span></a>
        <a href="#finder-papers" onClick={(event) => scrollToSection(event, "finder-papers")}>Papers <span>{data.papers_total}</span></a>
        <a href="#finder-training" onClick={(event) => scrollToSection(event, "finder-training")}>Training <span>{data.materials_total}</span></a>
      </nav>
      <Section id="finder-communities" title="Communities to contact" note={data.communities.length ? `Matched through their descriptions or tools tagged with ${area}. Communities matching more selected areas appear first.` : undefined}>
        {data.communities.length ? (
          <More items={data.communities} limit={4} render={(shown) => (
            <ol className="finder-communities">
              {shown.map((c) => <CommunityEntry key={c.id} community={c} />)}
            </ol>
          )} />
        ) : (
          <p className="empty">No ELIXIR Community is linked to {area} yet. Try a broader area.</p>
        )}
      </Section>
        <Section id="finder-resources" title="What these Communities point you to" note="Resources named on the matched Communities' pages or papers. These cover their wider work; they are not all specific to your selected area. Open the evidence to check the context.">
          {KINDS.map(([kind, title]) => {
            const items = data.resources.filter((r) => r.kind === kind);
            return items.length ? (
              <div className="finder-kind" key={kind}>
                <h3>{title}</h3>
                <More items={items} limit={5} render={(shown) => <ul className="finder-resources">
                  {shown.map((r) => (
                    <li key={r.id}>
                      <div className="finder-resource-title">
                        {r.url ? <a href={text(r.url)} target="_blank" rel="noreferrer">{r.name}</a> : <span>{r.name}</span>}
                        <a className="finder-record" href={recordHref("Resource", r.id)}>Record and sources</a>
                      </div>
                      <div className="finder-marks">
                        {r.by.map((b) => (
                          <Mark key={`${b.community}-${b.basis}`} basis={b} />
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>} />
              </div>
            ) : null;
          })}
          {!data.resources.length ? <p className="empty">No recommended or developed resources are linked to the matched Communities in this snapshot. Explore the topic-tagged tools below.</p> : null}
        </Section>
        <Section
          id="finder-tools"
          title="More tools for this area in bio.tools"
          note={`Tagged with ${area} in bio.tools, the ELIXIR tools registry. A listing is not a recommendation.${data.tools_total > data.tools.length ? ` Showing ${data.tools.length} of ${data.tools_total}.` : ""}`}
        >
          {data.tools.length ? <More
            items={data.tools}
            limit={12}
            render={(shown) => (
              <ul className="finder-resources">
                {shown.map((t) => (
                  <li key={t.id}>
                    <a href={text(t.homepage) || text(t.url)} target="_blank" rel="noreferrer">
                      {t.name}
                    </a>
                    <span className="finder-type">{list(t.tool_types).join(", ")}</span>
                    <span className="finder-marks">
                      {t.listed_for ? <span className="finder-mark listed">Listed for {text(t.listed_for)}</span> : null}
                      <a className="finder-mark plain" href={text(t.url)} target="_blank" rel="noreferrer">
                        bio.tools entry
                      </a>
                      <a className="finder-record" href={recordHref("Tool", t.id)}>Record and sources</a>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          /> : <p className="empty">No additional tools are tagged with these areas in this snapshot. Try another area or follow a Community's resources above.</p>}
        </Section>
        <Section id="finder-papers" title="Reports and papers from these Communities" note={`Outputs linked to the matched Communities, newest first. Check each paper's scope for relevance to your research.${capNote(data.papers.length, data.papers_total)}`}>
          {data.papers.length ? <More
            items={data.papers}
            limit={8}
            render={(shown) => (
              <ul className="finder-papers">
                {shown.map((p) => (
                  <li key={`${p.id}-${p.community}`}>
                    <a href={text(p.url)} target="_blank" rel="noreferrer">
                      {p.title}
                    </a>
                    <small>
                      {p.community}, {text(p.date).slice(0, 10)}
                    </small>
                    <a className="finder-record" href={recordHref("Output", p.id)}>Record and sources</a>
                  </li>
                ))}
              </ul>
            )}
          /> : <p className="empty">No reports or papers are linked to these Communities in this snapshot. Their Community pages may have more recent publications.</p>}
        </Section>
      <div className="finder-training" id="finder-training">
        <Section title="Training materials" note={`Tagged with your selected areas in the collected TeSS catalogue.${capNote(data.materials.length, data.materials_total)}`}>
          {data.materials.length ? (
            <More
              items={data.materials}
              limit={8}
              render={(shown) => (
                <ul className="finder-papers">
                  {shown.map((m) => (
                    <li key={m.id}>
                      <a href={text(m.url)} target="_blank" rel="noreferrer">
                        {m.title}
                      </a>
                      {m.content_provider || m.date_published ? <small>{[text(m.content_provider), text(m.date_published).slice(0, 10)].filter(Boolean).join(", ")}</small> : null}
                      <a className="finder-record" href={recordHref("TrainingMaterial", m.id)}>Record and sources</a>
                    </li>
                  ))}
                </ul>
              )}
            />
          ) : (
            <p className="empty">No training material is linked to these areas in this snapshot. Try another area or visit <a href="https://tess.elixir-europe.org/materials" target="_blank" rel="noreferrer">TeSS</a> for current listings.</p>
          )}
        </Section>
        <Section title="Upcoming events" note={`Events in the snapshot starting today or later, matched by topic.${capNote(data.events.length, data.events_total)}`}>
          {data.events.length ? (
            <More
              items={data.events}
              limit={8}
              render={(shown) => (
                <ul className="finder-papers">
                  {shown.map((e) => (
                    <li key={e.id}>
                      <a href={text(e.url)} target="_blank" rel="noreferrer">
                        {e.title}
                      </a>
                      <small>{[text(e.start).slice(0, 10), e.online ? "online" : [text(e.city), text(e.country)].filter(Boolean).join(", ")].filter(Boolean).join(", ")}</small>
                      <a className="finder-record" href={recordHref("Event", e.id)}>Record and sources</a>
                    </li>
                  ))}
                </ul>
              )}
            />
          ) : (
            <p className="empty">No upcoming event is linked to these areas in this snapshot. Check <a href="https://tess.elixir-europe.org/events" target="_blank" rel="noreferrer">TeSS</a> for current events.</p>
          )}
        </Section>
      </div>
      <p className="note finder-limits">
        This is a collected snapshot, not a live directory. Topics on Communities are assigned by a language model from their descriptions; topics on tools and training come from bio.tools and TeSS. A missing link does not mean there is no relevant work. Evidence is available on each record.
      </p>
    </>
  );
}

function CommunityEntry({ community: c }: { community: Community }) {
  const contacts = list(c.contacts);
  const emails = contacts.filter((x) => x.includes("@") && !x.startsWith("http"));
  return (
    <li className="finder-community">
      <div className="finder-community-head">
        <h3>
          <EntityLink id={c.id}>{c.name}</EntityLink>
        </h3>
        <p className="finder-why">
          {c.topics.length ? (
            <>
              Matched through its description: {" "}
              {c.topics.map((t, i) => (
                <span key={t.label} title={text(t.evidence)}>
                  {i ? ", " : ""}
                  {t.label}
                </span>
              ))}
              {c.tools ? `, with ${c.tools} ${c.tools === 1 ? "tool" : "tools"} in this area` : ""}
            </>
          ) : (
            `Has ${c.tools} ${c.tools === 1 ? "tool" : "tools"} in this area in bio.tools`
          )}
        </p>
      </div>
      <dl className="finder-contact">
        {c.leads?.length ? (
          <div>
            <dt>Contacts and leads</dt>
            <dd>
              {c.leads.map((l, i) => (
                <span key={l.id}>
                  {i ? ", " : ""}
                  <a href={href("person", l.id)} title={l.roles}>{l.name}</a>
                </span>
              ))}
            </dd>
          </div>
        ) : null}
        {emails.length ? (
          <div>
            <dt>Write to</dt>
            <dd>
              {emails.map((e, i) => (
                <span key={e}>
                  {i ? ", " : ""}
                  <a href={`mailto:${e}`}>{e}</a>
                </span>
              ))}
            </dd>
          </div>
        ) : null}
        {c.join_url || c.page ? (
          <div>
            <dt>Join</dt>
            <dd>
              {c.join_url ? (
                <a href={text(c.join_url)} target="_blank" rel="noreferrer">
                  Sign up as a member
                </a>
              ) : null}
              {c.join_url && c.page ? ", or read " : null}
              {c.page ? (
                <a href={text(c.page)} target="_blank" rel="noreferrer">
                  {c.join_url ? "the Community page" : "Read the Community page"}
                </a>
              ) : null}
            </dd>
          </div>
        ) : null}
      </dl>
      <details className="finder-evidence">
        <summary>Why this Community matches</summary>
        {c.topics.length ? c.topics.map((topic) => (
          <div key={topic.label}>
            <strong>{topic.label}</strong>
            {topic.evidence ? <blockquote>{text(topic.evidence)}</blockquote> : <p>No supporting excerpt is stored.</p>}
            <SourceLink url={topic.source_url} retrieved={topic.retrieved_at} />
            {topic.retrieved_at ? <small>Retrieved {text(topic.retrieved_at).slice(0, 10)}</small> : null}
          </div>
        )) : <p>This Community is linked through tools tagged with the selected area in bio.tools. A catalogue association is not a recommendation.</p>}
        <a href={href("initiative", c.id)}>Explore the Community and its sources</a>
      </details>
    </li>
  );
}

function Mark({ basis }: { basis: Basis }) {
  const name = basis.community.replace(/ Community$/, "");
  const says = [text(basis.purpose), text(basis.evidence)].filter(Boolean).join(": ");
  return (
    <details className={`finder-evidence finder-mark ${basis.basis === "develops" ? "develops" : "recommends"}`}>
      <summary>{basis.basis === "develops" ? "Developed by" : "Recommended by"} {name}</summary>
      <p>{says || "No supporting excerpt is stored."}</p>
      <SourceLink url={basis.source_url} />
    </details>
  );
}

function capNote(shown: number, total: number): string {
  return total > shown ? ` Showing the first ${shown} of ${total} matches.` : "";
}

function scrollToSection(event: MouseEvent<HTMLAnchorElement>, id: string) {
  event.preventDefault();
  const target = document.getElementById(id);
  target?.scrollIntoView({ block: "start" });
  target?.setAttribute("tabindex", "-1");
  target?.focus({ preventScroll: true });
}
