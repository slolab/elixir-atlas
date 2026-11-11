import type { Row } from "./db";

export type Named = { id: string; name: string };
export type KindCount = { kind: string; n: number };
export type Project = Named & { kind: string; start: string; end: string };
export type Role = { person: string; name: string; role_kind: string; role: string; work_item: string | null; funding: string; source_url: string; retrieved_at: string };
export type HomeData = { kinds: KindCount[]; nodes: (Named & { initiatives: number; people: number })[]; reviews: KindCount[]; projects: Project[] };
export type PersonData = {
  person: Row;
  nodes: Named[];
  roles: Row[];
  led: Row[];
  outputs: Row[];
  tools: Row[];
  organisations: { name: string }[];
  reviews: Row[];
};
export type NodeData = {
  node: Row;
  initiatives: (Named & { kind: string; family: string; start: string | null; end: string | null })[];
  people: (Named & { places: number; leads: number })[];
  tools: number;
  events: number;
  materials: number;
};
export type InitiativeData = {
  initiative: Row;
  roles: Role[];
  nodes: (Named & { sources: number })[];
  plan: Row[];
  leads: (Named & { plan: string })[];
  delivered: { plan: string; id: string; title: string; url: string }[];
  outputs: Row[];
  related: (Named & { kind: string; n: number })[];
  statements: Row[];
  topics: { label: string }[];
  tools: Row[];
  events: Row[];
  materials: Row[];
  reviews: Row[];
};
export type Listed = Named & { people: number; nodes: number; plan: number; start: string | null; end: string | null };
export type ReviewsData = { kinds: KindCount[]; active: string; items: Row[] };
export type OverlapData = {
  holders: (Named & { places: number; detail: string })[];
  pairs: { first: string; first_name: string; second: string; second_name: string; shared: number; people: string }[];
};
export type SearchData = {
  query: string;
  total: number;
  facets: { entity_type: string; count: number }[];
  hits: { entity_type: string; id: string; title: string; excerpt: string; url: string | null; score: number }[];
  limit: number;
  offset: number;
};
export type RecordData = {
  entity_type: string;
  title: string;
  record: Row;
  definition: { description: string; represented_as: string; source?: string; target?: string; biotope: { property_descriptions: Record<string, string> } };
  provenance: { mappings: string[]; evidence: { artifact: string; version: string; location: string; record_set?: string }[] };
};
export type RelationsData = {
  total: number;
  items: { relation_type: string; relation_id: string; direction: string; entity_type: string; id: string; title: string }[];
};
