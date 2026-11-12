import { useEffect, useState } from "react";

export type Route = { page: string; id: string };

function parse(): Route {
  const [, page = "", ...rest] = window.location.hash.split("/");
  return { page: page || "home", id: decodeURIComponent(rest.join("/")) };
}

export function useRoute(): Route {
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const update = () => {
      const next = parse();
      setRoute((previous) => {
        if (previous.page !== next.page || (previous.id !== next.id && next.page !== "search")) {
          window.scrollTo(0, 0);
        }
        return next;
      });
    };
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return route;
}

export function href(page: string, id = ""): string {
  return id ? `#/${page}/${encodeURIComponent(id)}` : `#/${page}`;
}

export function updateRequestHref({ entityType, entityId, context = "", from = "#/" }: { entityType?: string; entityId?: string; context?: string; from?: string }) {
  const params = new URLSearchParams({ context, from });
  if (entityType && entityId) {
    params.set("type", entityType);
    params.set("id", entityId);
  }
  return href("request-update", params.toString());
}

const PAGES: Record<string, string> = { initiative: "initiative", person: "person", node: "node" };

export function entityHref(id: string): string | null {
  const page = PAGES[id.split(":", 1)[0]];
  return page ? href(page, id) : null;
}

export function recordHref(type: string, id: string): string {
  const pages: Record<string, string> = { Initiative: "initiative", Person: "person", ElixirNode: "node" };
  return pages[type] ? href(pages[type], id) : href("record", `${type}/${id}`);
}

export function typeLabel(type: string): string {
  return type === "ElixirNode" ? "ELIXIR Node" : type.replace(/([a-z])([A-Z])/g, "$1 $2");
}
