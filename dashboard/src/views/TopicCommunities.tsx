import { EntityLink, More, Section, SourceLink } from "../components";
import { list, type Value } from "../db";
import { text } from "../format";
import { href } from "../route";

export type Community = {
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

export function TopicCommunities({ communities, area }: { communities: Community[]; area: string }) {
  return (
    <Section id="finder-communities" title="Communities to contact" note={communities.length ? `Matched through their descriptions or tools tagged with ${area}. Communities matching more selected areas appear first.` : undefined}>
      {communities.length ? (
        <More items={communities} limit={4} render={(shown) => (
          <ol className="finder-communities">
            {shown.map((c) => <CommunityEntry key={c.id} community={c} />)}
          </ol>
        )} />
      ) : (
        <p className="empty">No ELIXIR Community is linked to {area} yet. Try a broader area.</p>
      )}
    </Section>
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
