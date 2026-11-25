import { useEffect, useState } from "react";
import { href, updateRequestHref, useRoute } from "./route";
import { Home } from "./views/Home";
import { PortfolioPage } from "./views/Portfolio";
import { InitiativePage } from "./views/Initiative";
import { NodePage } from "./views/Node";
import { Overlap } from "./views/Overlap";
import { PersonPage } from "./views/Person";
import { Reviews } from "./views/Reviews";
import { RecordPage } from "./views/Record";
import { KindList, Search } from "./views/Search";
import { UpdateRequestPage } from "./UpdateRequest";
import { TopicPage } from "./views/Topic";

export function App() {
  const route = useRoute();
  const types: Record<string, string> = { person: "Person", initiative: "Initiative", node: "ElixirNode" };
  const [recordType, ...recordId] = route.id.split("/");
  const entityType = route.page === "record" ? recordType : types[route.page];
  const entityId = route.page === "record" ? recordId.join("/") : entityType ? route.id : undefined;
  const requestLink = route.page === "request-update" ? href(route.page, route.id) : updateRequestHref({ entityType, entityId, context: href(route.page, route.id), from: href(route.page, route.id) });
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); document.getElementById("main-content")?.focus(); }}>Skip to main content</a>
      <Notice />
      <Masthead query={route.page === "search" ? route.id : ""} page={route.page} />
      <Navigation page={route.page} requestLink={requestLink} />
      <main className="page" id="main-content" tabIndex={-1}>
        <View page={route.page} id={route.id} key={route.page} />
      </main>
    </div>
  );
}

function View({ page, id }: { page: string; id: string }) {
  switch (page) {
    case "request-update":
      return <UpdateRequestPage value={id} key={id} />;
    case "topic":
      return <TopicPage id={id} />;
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
    case "portfolio":
      return <PortfolioPage id={id} />;
    case "overlap":
      return <Overlap />;
    case "reviews":
      return <Reviews kind={id} />;
    default:
      return <Home />;
  }
}

function Notice() {
  return (
    <aside className="notice" aria-label="About this information">
      <p>
        <strong>AI-compiled content.</strong> The information in this atlas was compiled using AI and has not been independently checked or validated by humans. It may contain inaccuracies.
      </p>
      <p>
        For official ELIXIR information, visit <a href="https://elixir-europe.org" target="_blank" rel="noopener">elixir-europe.org</a>.
      </p>
    </aside>
  );
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
      <a className="brand" href="#/" aria-label="ELIXIR Atlas home">
        <img src="/brand/elixir-atlas-logo.svg" alt="ELIXIR Atlas" width="440" height="132" />
      </a>
      <form className="search" role="search" onSubmit={(event) => event.preventDefault()}>
        <label htmlFor="search" className="visually-hidden">
          Search the atlas
        </label>
        <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>
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
    </header>
  );
}

function Navigation({ page, requestLink }: { page: string; requestLink: string }) {
  const navigation = [
    { page: "home", title: "Home", icon: "m3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9" },
    { page: "portfolio", title: "Node portfolio", icon: "M3 7h18v13H3zM8 7V4h8v3M3 13h18" },
    { page: "topic", title: "Find by topic", icon: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm4 5-2 6-6 2 2-6 6-2Z" },
    { page: "overlap", title: "Shared leadership", icon: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm8 1a4 4 0 0 1 0 7m1 4a4 4 0 0 1 4 4v2" },
    { page: "reviews", title: "Data review", icon: "M9 5h12M9 12h12M9 19h12M2 5l1 1 3-3M2 12l1 1 3-3M2 19l1 1 3-3" },
  ];
  return (
    <nav className="nav" aria-label="Main navigation">
      <div className="nav-inner">
        {navigation.map((item) => <a key={item.page} href={item.page === "home" ? "#/" : href(item.page)} aria-current={page === item.page ? "page" : undefined} onClick={() => { if (page === item.page) window.scrollTo(0, 0); }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={item.icon} /></svg>
          {item.title}
        </a>)}
        <a className="feedback-link" href={requestLink} aria-current={page === "request-update" ? "page" : undefined}>Request update</a>
        <p className="nav-note">
          This page is a proof of concept created by project 26 of the ELIXIR BioHackathon 2026 and will not be regularly updated. The source code is available at <a href="https://github.com/slolab/elixir-atlas" target="_blank" rel="noopener">github.com/slolab/elixir-atlas</a>.
        </p>
      </div>
    </nav>
  );
}
