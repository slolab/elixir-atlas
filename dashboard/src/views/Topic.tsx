import { useId, useMemo, useState, type MouseEvent } from "react";
import { More, RequestState, Section } from "../components";
import { apiUrl, type Value, useApi } from "../db";
import { text } from "../format";
import { href, recordHref } from "../route";
import { TopicCommunities, type Community } from "./TopicCommunities";
import { TopicResources, type Resource, type Tool } from "./TopicResources";

type TopicRow = { id: string; label: string; communities: number; tools: number; materials: number };
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
      <TopicCommunities communities={data.communities} area={area} />
      <TopicResources resources={data.resources} tools={data.tools} toolsTotal={data.tools_total} area={area} />
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
