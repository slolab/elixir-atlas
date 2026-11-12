import { useEffect, useState } from "react";
import { href, useRoute } from "./route";
import { Home } from "./views/Home";
import { InitiativePage } from "./views/Initiative";
import { NodePage } from "./views/Node";
import { Overlap } from "./views/Overlap";
import { PersonPage } from "./views/Person";
import { Reviews } from "./views/Reviews";
import { RecordPage } from "./views/Record";
import { KindList, Search } from "./views/Search";
import { apiUrl, useApi } from "./db";
import { UpdateRequest, UpdateRequestsEnabled } from "./UpdateRequest";

export function App() {
  const route = useRoute();
  const { data, error } = useApi<{ api: { update_requests: boolean } }>(apiUrl("release"));
  const types: Record<string, string> = { person: "Person", initiative: "Initiative", node: "ElixirNode" };
  const [recordType, ...recordId] = route.id.split("/");
  const entityType = route.page === "record" ? recordType : types[route.page];
  const entityId = route.page === "record" ? recordId.join("/") : entityType ? route.id : undefined;
  return (
    <UpdateRequestsEnabled.Provider value={error ? false : data?.api.update_requests}>
      <Masthead query={route.page === "search" ? route.id : ""} page={route.page} />
      <main className="page">
        <UpdateRequest key={`${route.page}/${route.id}`} entityType={entityType} entityId={entityId} context={href(route.page, route.id)} />
        <View page={route.page} id={route.id} key={route.page} />
      </main>
    </UpdateRequestsEnabled.Provider>
  );
}

function View({ page, id }: { page: string; id: string }) {
  switch (page) {
    case "record":
      return <RecordPage value={id} />;
    case "initiative":
      return <InitiativePage id={id} />;
    case "person":
      return <PersonPage id={id} />;
    case "node":
      return <NodePage id={id} />;
    case "search":
      return <Search query={id} />;
    case "kind":
      return <KindList kind={id} />;
    case "overlap":
      return <Overlap />;
    case "reviews":
      return <Reviews kind={id} />;
    default:
      return <Home />;
  }
}

function Masthead({ query, page }: { query: string; page: string }) {
  const [value, setValue] = useState(query);
  useEffect(() => setValue(query), [query]);
  const search = (next: string) => {
    setValue(next);
    const target = href("search", next.trim());
    if (page === "search") {
      window.history.replaceState(null, "", target);
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    } else if (next.trim().length > 1) {
      window.location.hash = target;
    }
  };
  return (
    <header className="masthead">
      <a className="brand" href="#/">
        ELIXIR Atlas
      </a>
      <form className="search" role="search" onSubmit={(event) => event.preventDefault()}>
        <label htmlFor="search" className="visually-hidden">
          Search the atlas
        </label>
        <input
          id="search"
          type="search"
          autoComplete="off"
          maxLength={200}
          placeholder="Search the atlas"
          value={value}
          onChange={(event) => search(event.target.value)}
        />
      </form>
      <nav className="nav">
        <a href={href("overlap")} aria-current={page === "overlap" ? "page" : undefined}>
          Overlap
        </a>
        <a href={href("reviews")} aria-current={page === "reviews" ? "page" : undefined}>
          Review queue
        </a>
      </nav>
    </header>
  );
}
