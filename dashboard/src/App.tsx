import { useEffect, useState } from "react";
import { openAtlas } from "./db";
import { href, useRoute } from "./route";
import { Home } from "./views/Home";
import { InitiativePage } from "./views/Initiative";
import { NodePage } from "./views/Node";
import { Overlap } from "./views/Overlap";
import { PersonPage } from "./views/Person";
import { Reviews } from "./views/Reviews";
import { KindList, Search } from "./views/Search";

type State = { status: "loading" } | { status: "ready" } | { status: "failed"; message: string };

export function App() {
  const [state, setState] = useState<State>({ status: "loading" });
  const route = useRoute();
  useEffect(() => {
    openAtlas().then(
      () => setState({ status: "ready" }),
      (error: unknown) => setState({ status: "failed", message: error instanceof Error ? error.message : String(error) }),
    );
  }, []);
  return (
    <>
      <Masthead query={route.page === "search" ? route.id : ""} page={route.page} />
      <main className="page">
        {state.status === "loading" ? <p className="status">Opening the atlas database…</p> : null}
        {state.status === "failed" ? (
          <div className="status failed">
            <p>The atlas database could not be opened.</p>
            <p>{state.message}</p>
          </div>
        ) : null}
        {state.status === "ready" ? <View page={route.page} id={route.id} /> : null}
      </main>
    </>
  );
}

function View({ page, id }: { page: string; id: string }) {
  switch (page) {
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
          Search groups, projects, people and Nodes
        </label>
        <input
          id="search"
          type="search"
          autoComplete="off"
          placeholder="Search groups, projects, people and Nodes"
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
