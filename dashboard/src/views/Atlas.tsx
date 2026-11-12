import { useMemo, useState } from "react";
import { RequestState, SourceLink } from "../components";
import { apiUrl, type Row, useApi } from "../db";
import { label, text } from "../format";
import { recordHref } from "../route";

type Card = { id: string; label: string; description: string; table: string; count: number };
type RouteDef = { id: string; source: string; target: string; description: string; properties: string[] };
type Question = { id: string; use_case: string; question: string; cards: string[]; routes: string[] };
type Overview = { questions: Question[]; cards: Record<string, Card>; routes: Record<string, RouteDef> };
type Link = { route: string; from: string; to: string; properties: Record<string, unknown>; evidence?: string; source_url?: string; retrieved_at?: string };
type Picked = { question: string; cards: Record<string, { filtered: boolean; total: number; items: Row[] }>; links: Link[]; links_total: number };
type Pick = { card: string; id: string; title: string };

const GROUPS: Record<string, string> = {
  A: "A · Communities Coordinator",
  B: "B · Node team",
  C1: "C1 · Researcher",
  C2: "C2 · Community co-lead",
};

export function Atlas() {
  const { data, error } = useApi<Overview>(apiUrl("atlas"));
  const [questionId, setQuestionId] = useState("");
  if (!data) return <RequestState error={error} />;
  const question = data.questions.find((q) => q.id === questionId);
  return (
    <>
      <h1 className="page-title">Atlas</h1>
      <p className="lede">
        The competency questions, answered on the built graph. Pick a question to see its cards; pick an item on a card and every other card narrows to what
        the question's routes connect to it. Pick on several cards to intersect. Each connection shows its source.
      </p>
      <div className="atlas">
        <QuestionList questions={data.questions} current={questionId} onPick={setQuestionId} />
        <div className="atlas-main">
          {question ? <Board key={question.id} question={question} overview={data} /> : <p className="empty">Choose a question.</p>}
        </div>
      </div>
    </>
  );
}

function QuestionList({ questions, current, onPick }: { questions: Question[]; current: string; onPick: (id: string) => void }) {
  const group = (q: Question) => (q.use_case.startsWith("C") ? q.use_case.slice(0, 2) : q.use_case[0]);
  const groups = Object.keys(GROUPS).map((g) => [g, questions.filter((q) => group(q) === g)] as const);
  return (
    <nav className="atlas-questions" aria-label="Competency questions">
      {groups.map(([g, qs]) =>
        qs.length ? (
          <section key={g}>
            <h2>{GROUPS[g]}</h2>
            <ol>
              {qs.map((q) => (
                <li key={q.id}>
                  <button type="button" aria-pressed={q.id === current} onClick={() => onPick(q.id)}>
                    <span className="cq-id">{q.use_case}</span> {q.question}
                  </button>
                </li>
              ))}
            </ol>
          </section>
        ) : null,
      )}
    </nav>
  );
}

function Board({ question, overview }: { question: Question; overview: Overview }) {
  const [picks, setPicks] = useState<Pick[]>([]);
  const param = picks.map((p) => `${p.card}=${p.id}`).join(",");
  const { data, error } = useApi<Picked>(apiUrl("atlas/pick", { question: question.id, picks: param }));
  const pickedIds = useMemo(() => new Set(picks.map((p) => p.id)), [picks]);
  const toggle = (card: string, row: Row) => {
    const id = text(row.id);
    setPicks((now) => (now.some((p) => p.id === id) ? now.filter((p) => p.id !== id) : [...now, { card, id, title: text(row.title) }]));
  };
  const routes = question.routes.map((r) => overview.routes[r]).filter(Boolean);
  return (
    <>
      <h2 className="atlas-question">
        <span className="cq-id">{question.use_case}</span> {question.question}
      </h2>
      <p className="note">
        Routes:{" "}
        {routes.map((r, i) => (
          <span key={r.id} title={r.description}>
            {i ? " · " : ""}
            {label(r.source)} → <b>{r.id}</b> → {label(r.target)}
          </span>
        ))}
      </p>
      {picks.length ? (
        <p className="atlas-picks">
          Picked:{" "}
          {picks.map((p) => (
            <button key={p.id} type="button" onClick={() => setPicks((now) => now.filter((x) => x.id !== p.id))} title="Remove this pick">
              {overview.cards[p.card]?.label}: {p.title} ×
            </button>
          ))}
          <button type="button" className="clear" onClick={() => setPicks([])}>
            Clear
          </button>
        </p>
      ) : null}
      {!data ? <RequestState error={error} /> : null}
      <div className="atlas-cards">
        {question.cards.map((cardId) => (
          <CardColumn key={cardId} card={overview.cards[cardId]} data={data?.cards[cardId]} picked={pickedIds} onToggle={(row) => toggle(cardId, row)} />
        ))}
      </div>
      {data && picks.length ? <Evidence links={data.links} total={data.links_total} titles={titles(data, picks)} /> : null}
    </>
  );
}

function CardColumn({ card, data, picked, onToggle }: { card: Card; data?: { filtered: boolean; total: number; items: Row[] }; picked: Set<string>; onToggle: (row: Row) => void }) {
  const [filter, setFilter] = useState("");
  const items = (data?.items ?? []).filter((r) => !filter || text(r.title).toLowerCase().includes(filter.toLowerCase()));
  return (
    <section className="atlas-card" aria-label={card.label}>
      <header>
        <h3 title={card.description}>{card.label}</h3>
        <span className="count">
          {data ? (data.filtered ? `${data.total} of ${card.count}` : card.count) : "…"}
        </span>
      </header>
      <input type="search" placeholder={`Find ${card.label.toLowerCase()}`} value={filter} onChange={(e) => setFilter(e.target.value)} />
      {data && data.filtered && data.total === 0 ? <p className="empty">No public record linked along this question's routes. That is not proof there is none.</p> : null}
      <ul>
        {items.map((row) => {
          const id = text(row.id);
          const details = Object.entries(row)
            .filter(([k, v]) => !["id", "title"].includes(k) && v !== null && v !== "")
            .map(([k, v]) => (k === "kind" || k === "status" ? label(text(v)) : text(v)))
            .join(" · ");
          return (
            <li key={id}>
              <button type="button" aria-pressed={picked.has(id)} onClick={() => onToggle(row)}>
                {text(row.title) || id}
                {details ? <small>{details}</small> : null}
              </button>
              <a className="open" href={recordHref(card.table, id)} title="Open the record">
                ↗
              </a>
            </li>
          );
        })}
      </ul>
      {data && data.total > data.items.length ? <p className="note">Showing {data.items.length} of {data.total}; type to find others or pick on another card to narrow.</p> : null}
    </section>
  );
}

function titles(data: Picked, picks: Pick[]): Map<string, string> {
  const out = new Map(picks.map((p) => [p.id, p.title]));
  for (const card of Object.values(data.cards)) for (const r of card.items) out.set(text(r.id), text(r.title));
  return out;
}

function Evidence({ links, total, titles }: { links: Link[]; total: number; titles: Map<string, string> }) {
  return (
    <section className="section">
      <header className="section-head">
        <h2>Connections and their sources</h2>
        <p className="note">{total > links.length ? `First ${links.length} of ${total}.` : `${total} connections.`} One row per relationship record; several records may state the same connection.</p>
      </header>
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Route</th>
            <th scope="col">From → to</th>
            <th scope="col">Details</th>
            <th scope="col">Evidence</th>
            <th scope="col">Source</th>
          </tr>
        </thead>
        <tbody>
          {links.map((l, i) => (
            <tr key={`${l.route}-${l.from}-${l.to}-${i}`}>
              <td>{l.route}</td>
              <td>
                {titles.get(l.from) ?? l.from} → {titles.get(l.to) ?? l.to}
              </td>
              <td>
                {Object.entries(l.properties)
                  .map(([k, v]) => `${label(k)}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
                  .join(" · ")}
              </td>
              <td className="quote">{text(l.evidence as string)}</td>
              <td>
                <SourceLink url={l.source_url} retrieved={l.retrieved_at} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
