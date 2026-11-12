import { useMemo, useState, type KeyboardEvent, type MouseEvent } from "react";
import { month, monthName, text } from "./format";
import { href } from "./route";

type Project = { id: string; name: string; kind: string; start: string; end: string };

const TRACES = [
  { key: "services", label: "Commissioned services", short: "commissioned services", kinds: ["commissioned_service"] },
  { key: "eu", label: "EU projects", short: "EU projects", kinds: ["eu_project"] },
  { key: "exchange", label: "Staff exchanges", short: "staff exchanges", kinds: ["staff_exchange"] },
];

const WIDTH = 1200;
const HEIGHT = 240;
const TOP = 12;
const BOTTOM = 28;
const TODAY = new Date().getFullYear() * 12 + new Date().getMonth();

function smooth(values: number[], sigma: number): number[] {
  const radius = Math.ceil(sigma * 3);
  const weights = Array.from({ length: radius * 2 + 1 }, (_, index) => Math.exp(-((index - radius) ** 2) / (2 * sigma * sigma)));
  return values.map((_, center) => {
    let total = 0;
    let weight = 0;
    weights.forEach((w, index) => {
      const at = center + index - radius;
      if (at >= 0 && at < values.length) {
        total += values[at] * w;
        weight += w;
      }
    });
    return total / weight;
  });
}

export function Chromatogram({ projects: source }: { projects: Project[] }) {
  const data = useMemo(() => {
    const projects = source
      .map((project) => ({ ...project, from: month(project.start, "start")!, to: month(project.end, "end")! }))
      .filter((project) => project.from <= project.to);
    const first = Math.max(2014 * 12, Math.min(...projects.map((project) => project.from)));
    const last = Math.min(2029 * 12 + 11, Math.max(...projects.map((project) => project.to)));
    const span = last - first + 1;
    const raw = TRACES.map((trace) => {
      const counts = new Array<number>(span).fill(0);
      for (const project of projects) {
        if (trace.kinds.includes(project.kind)) {
          for (let at = Math.max(project.from, first); at <= Math.min(project.to, last); at += 1) {
            counts[at - first] += 1;
          }
        }
      }
      return counts;
    });
    const curves = raw.map((counts) => smooth(counts, 1.6));
    const peak = Math.max(1, ...curves.flat());
    return { projects, first, last, span, raw, curves, peak };
  }, [source]);

  const [hover, setHover] = useState<number | null>(null);
  const [picked, setPicked] = useState(() => Math.min(Math.max(TODAY, data.first), data.last));
  const shown = hover ?? picked;
  const x = (at: number) => ((at - data.first) / Math.max(1, data.span - 1)) * WIDTH;
  const y = (value: number) => TOP + (1 - value / data.peak) * (HEIGHT - TOP - BOTTOM);
  const years = Array.from({ length: Math.floor(data.last / 12) - Math.ceil(data.first / 12) + 1 }, (_, index) => Math.ceil(data.first / 12) + index);

  const monthAt = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - box.left) / box.width));
    return data.first + Math.round(ratio * (data.span - 1));
  };

  const onKey = (event: KeyboardEvent<SVGSVGElement>) => {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (step) {
      event.preventDefault();
      setPicked((current) => Math.min(data.last, Math.max(data.first, current + step * (event.shiftKey ? 12 : 1))));
    }
  };

  const running = data.projects
    .filter((project) => project.from <= picked && picked <= project.to)
    .sort((left, right) => left.from - right.from || left.name.localeCompare(right.name));

  return (
    <div className="chromatogram">
      <p className="readout" aria-live="polite">
        <strong>{monthName(shown)}</strong>
        {TRACES.map((trace, index) => (
          <span key={trace.key} className={`readout-item trace-${trace.key}`}>
            {data.raw[index][shown - data.first]} {trace.short}
          </span>
        ))}
      </p>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        role="slider"
        tabIndex={0}
        aria-label="Month"
        aria-valuemin={data.first}
        aria-valuemax={data.last}
        aria-valuenow={picked}
        aria-valuetext={monthName(picked)}
        onPointerMove={(event) => setHover(monthAt(event))}
        onPointerLeave={() => setHover(null)}
        onClick={(event) => setPicked(monthAt(event))}
        onKeyDown={onKey}
      >
        {years.map((year) => (
          <line key={year} className="year-rule" x1={x(year * 12)} x2={x(year * 12)} y1={TOP} y2={HEIGHT - BOTTOM} />
        ))}
        {data.curves.map((curve, index) => (
          <path
            key={TRACES[index].key}
            className={`trace trace-${TRACES[index].key}`}
            style={{ animationDelay: `${index * 180}ms` }}
            pathLength={1}
            d={curve.map((value, at) => `${at ? "L" : "M"}${x(data.first + at).toFixed(1)},${y(value).toFixed(1)}`).join("")}
          />
        ))}
        <line className="baseline" x1={0} x2={WIDTH} y1={HEIGHT - BOTTOM} y2={HEIGHT - BOTTOM} />
        {TODAY >= data.first && TODAY <= data.last ? (
          <line className="today" x1={x(TODAY)} x2={x(TODAY)} y1={TOP} y2={HEIGHT - BOTTOM} />
        ) : null}
        <line className="cursor" x1={x(shown)} x2={x(shown)} y1={TOP - 8} y2={HEIGHT - BOTTOM} />
      </svg>
      <div className="years" aria-hidden="true">
        {years.map((year) => (
          <span key={year} style={{ left: `${(x(year * 12) / WIDTH) * 100}%` }} className={year % 2 ? "odd" : ""}>
            {year}
          </span>
        ))}
      </div>
      <div className="running">
        <h2>Running in {monthName(picked)}</h2>
        <p className="note">Click the chart or use the arrow keys to pick another month. Shift moves a year.</p>
        {TRACES.map((trace) => {
          const items = running.filter((project) => trace.kinds.includes(project.kind));
          return (
            <div key={trace.key} className={`running-group trace-${trace.key}`}>
              <h3>
                {trace.label} <span className="count">{items.length}</span>
              </h3>
              <ul>
                {items.map((project) => (
                  <li key={project.id}>
                    <a href={href("initiative", project.id)}>{project.name}</a>
                    <span className="dates">
                      {text(project.start)} to {text(project.end)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
