import type { Value } from "./db";

const LABELS: Record<string, string> = {
  eu_project: "EU project",
  node_group: "Node group",
  node_programme: "Node programme",
  node_project: "Node project",
  other_group: "Other group",
  lead_node: "Lead's Node",
  co_lead: "Co-lead",
  head_of_node: "Head of Node",
  person_match: "Same person?",
  initiative_match: "Same group or project?",
  organisation_match: "Same organisation?",
  value_conflict: "Sources disagree",
  not_stated: "Not stated",
  in_kind: "In kind",
  zenodo_record: "Zenodo record",
  embl_ebi: "EMBL-EBI",
  member_node: "Member Node",
  hub: "ELIXIR Hub",
};

export function label(value: Value | undefined): string {
  if (typeof value !== "string" || !value) {
    return "";
  }
  if (LABELS[value]) {
    return LABELS[value];
  }
  const words = value.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export function text(value: Value | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

export function period(start: Value | undefined, end: Value | undefined): string {
  if (!start && !end) {
    return "";
  }
  return `${text(start) || "unknown"} to ${text(end) || "unknown"}`;
}

export function count(value: number, one: string, many: string): string {
  return `${value.toLocaleString("en")} ${value === 1 ? one : many}`;
}

export function euros(value: Value | undefined): string {
  return typeof value === "number" ? `€${Math.round(value).toLocaleString("en")}` : "";
}

export function month(date: Value | undefined, edge: "start" | "end"): number | null {
  const match = /^(\d{4})(?:-(\d{2}))?/.exec(text(date));
  if (!match) {
    return null;
  }
  const monthOfYear = match[2] ? Number(match[2]) : edge === "start" ? 1 : 12;
  return Number(match[1]) * 12 + monthOfYear - 1;
}

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export function monthName(index: number): string {
  return `${MONTHS[index % 12]} ${Math.floor(index / 12)}`;
}

export function pageLabel(url: Value | undefined): string {
  try {
    const parsed = new URL(text(url));
    const parts = parsed.pathname.split("/").filter(Boolean);
    const site = parsed.hostname.replace(/^www\./, "");
    const last = parts.length ? decodeURIComponent(parts[parts.length - 1]) : "";
    const tail = parsed.search && last.length < 40 ? `${last}${parsed.search}` : last;
    return !tail ? site : parts.length > 1 ? `${site}/…/${tail}` : `${site}/${tail}`;
  } catch {
    return text(url);
  }
}

export function host(url: Value | undefined): string {
  try {
    return new URL(text(url)).hostname.replace(/^www\./, "");
  } catch {
    return text(url);
  }
}
