import { More, Section, SourceLink } from "../components";
import { list, type Value } from "../db";
import { text } from "../format";
import { recordHref } from "../route";

type Basis = { community: string; basis: string; purpose: Value; evidence: Value; source_url: Value };
export type Resource = { id: string; name: string; kind: string; url: Value; by: Basis[] };
export type Tool = { id: string; name: string; homepage: Value; url: Value; tool_types: Value; listed_for: Value };

const KINDS: [string, string][] = [
  ["standard", "Standards"],
  ["guideline", "Guidelines"],
  ["practice", "Good practice"],
  ["database", "Databases and registries"],
  ["tool", "Tools"],
  ["training", "Training resources"],
  ["document", "Documents"],
];

export function TopicResources({ resources, tools, toolsTotal, area }: { resources: Resource[]; tools: Tool[]; toolsTotal: number; area: string }) {
  return (
    <>
      <Section id="finder-resources" title="What these Communities point you to" note="Resources named on the matched Communities' pages or papers. These cover their wider work; they are not all specific to your selected area. Open the evidence to check the context.">
        {KINDS.map(([kind, title]) => {
          const items = resources.filter((r) => r.kind === kind);
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
        {!resources.length ? <p className="empty">No recommended or developed resources are linked to the matched Communities in this snapshot. Explore the topic-tagged tools below.</p> : null}
      </Section>
      <Section
        id="finder-tools"
        title="More tools for this area in bio.tools"
        note={`Tagged with ${area} in bio.tools, the ELIXIR tools registry. A listing is not a recommendation.${toolsTotal > tools.length ? ` Showing ${tools.length} of ${toolsTotal}.` : ""}`}
      >
        {tools.length ? <More
          items={tools}
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
    </>
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
