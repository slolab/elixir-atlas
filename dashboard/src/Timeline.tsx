import type { Row } from "./db";
import { label, month, monthName, text } from "./format";

const ORDER = ["work_package", "task", "deliverable", "milestone", "event", "output", "action", "goal", "open_item"];
const TODAY = new Date().getFullYear() * 12 + new Date().getMonth();

type Point = { kind: string; at: number; items: Row[] };

export function Timeline({ items, start, end }: { items: Row[]; start: unknown; end: unknown }) {
  const points = new Map<string, Point>();
  for (const item of items) {
    const at = /^\d{4}-\d{2}/.test(text(item.date)) ? month(item.date, "start") : null;
    if (at !== null) {
      const key = `${text(item.kind)}/${at}`;
      const point = points.get(key) ?? { kind: text(item.kind), at, items: [] };
      point.items.push(item);
      points.set(key, point);
    }
  }
  const dated = [...points.values()];
  if (!dated.length) {
    return null;
  }
  const total = dated.reduce((sum, point) => sum + point.items.length, 0);
  const from = Math.min(...dated.map((point) => point.at), month(start as string, "start") ?? Infinity);
  const to = Math.max(...dated.map((point) => point.at), month(end as string, "end") ?? -Infinity);
  const lanes = ORDER.filter((kind) => dated.some((point) => point.kind === kind));
  const width = 1000;
  const lane = 34;
  const left = 150;
  const height = lanes.length * lane + 30;
  const x = (at: number) => left + ((at - from) / Math.max(1, to - from)) * (width - left - 20);
  const years = Array.from({ length: Math.floor(to / 12) - Math.ceil(from / 12) + 1 }, (_, index) => Math.ceil(from / 12) + index);
  return (
    <figure className="timeline">
      <div className="timeline-scroll">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${total} dated plan items from ${monthName(from)} to ${monthName(to)}`}>
          {years.map((year) => (
            <g key={year}>
              <line className="year-rule" x1={x(year * 12)} x2={x(year * 12)} y1={0} y2={height - 24} />
              {x(year * 12) < width - 50 ? (
                <text className="axis" x={x(year * 12) + 4} y={height - 8}>
                  {year}
                </text>
              ) : null}
            </g>
          ))}
          {TODAY >= from && TODAY <= to ? <line className="today" x1={x(TODAY)} x2={x(TODAY)} y1={0} y2={height - 24} /> : null}
          {lanes.map((kind, index) => (
            <g key={kind}>
              <text className="lane" x={0} y={index * lane + 21}>
                {label(kind)}
              </text>
              <line className="lane-rule" x1={left} x2={width - 20} y1={index * lane + 17} y2={index * lane + 17} />
              {dated
                .filter((point) => point.kind === kind)
                .map((point) => {
                  const done = point.items.every((item) => item.status === "done");
                  return (
                    <g key={point.at}>
                      <circle className={done ? "dot done" : "dot"} cx={x(point.at)} cy={index * lane + 17} r={Math.min(13, 4.5 + 2.2 * Math.sqrt(point.items.length - 1))}>
                        <title>
                          {monthName(point.at)}:{" "}
                          {point.items.map((item) => [item.code, item.label].filter(Boolean).join(" ") + ` (${label(item.status).toLowerCase()})`).join("; ")}
                        </title>
                      </circle>
                      {point.items.length > 1 ? (
                        <text className={done ? "dot-count done" : "dot-count"} x={x(point.at)} y={index * lane + 21}>
                          {point.items.length}
                        </text>
                      ) : null}
                    </g>
                  );
                })}
            </g>
          ))}
        </svg>
      </div>
      <figcaption className="note">
        Each dot is one month; a number shows several items due then. Filled dots are done, and the dashed line is today. {items.length - total} plan items have no month and are only in the list below.
      </figcaption>
    </figure>
  );
}
