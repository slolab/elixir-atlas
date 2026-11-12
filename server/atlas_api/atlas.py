from pathlib import Path

import yaml

from .views import rows

QUESTIONS_PATH = Path(__file__).parent / "atlas_questions.yaml"

CARDS = {
    "initiative": ("Initiative", None, "name", ["kind", "start", "end", "status"], "Initiative", "An ELIXIR group or project of any kind."),
    "community": ("Initiative", "kind='community'", "name", ["start", "end", "status"], "Community", "An ELIXIR Community (Initiative of kind community)."),
    "platform": ("Initiative", "kind='platform'", "name", ["start", "end", "status"], "Platform", "An ELIXIR Platform (Initiative of kind platform)."),
    "focus_group": ("Initiative", "kind='focus_group'", "name", ["start", "end", "status"], "Focus Group", "An ELIXIR Focus Group (Initiative of kind focus_group)."),
    "project": ("Initiative", "family='project'", "name", ["kind", "start", "end", "status"], "Project", "A project: EU project, Commissioned Service, Implementation Study, staff exchange, Node project (Initiative of family project)."),
    "person": ("Person", None, "name", [], "Person", "A person named by at least one source."),
    "node": ("ElixirNode", None, "name", ["country"], "ELIXIR Node", "An ELIXIR Node or the Hub."),
    "organisation": ("Organisation", None, "name", ["country"], "Organisation", "A CORDIS participant or an affiliation a source gives."),
    "plan_item": ("PlanItem", None, "label", ["code", "kind", "date", "status"], "Plan item", "Work package, task, deliverable, milestone or other planned work of one initiative."),
    "output": ("Output", None, "title", ["date", "resource_type"], "Output", "A Zenodo or F1000 record."),
    "tool": ("Tool", None, "name", [], "Tool", "A bio.tools entry with an ELIXIR tag."),
    "event": ("TrainingEvent", None, "title", ["start", "country"], "Training event", "An event listed in TeSS."),
    "material": ("TrainingMaterial", None, "title", ["date_published"], "Training material", "A material listed in TeSS."),
    "topic": ("Topic", None, "label", ["uri"], "Topic", "An EDAM topic."),
    "statement": ("SourceStatement", None, "name_as_written", ["kind", "status", "start", "end", "retrieved_at"], "Source statement", "What one page or document states about one group or project."),
}

EVIDENCE = ("evidence", "source_url", "retrieved_at", "source_document")
EDGE_FIXED = {"id", "source", "target", "biotope_provenance_id", *EVIDENCE}
MAX_ITEMS = 400
MAX_LINKS = 300


def ident(name):
    return '"' + name.replace('"', '""') + '"'


def questions():
    return yaml.safe_load(QUESTIONS_PATH.read_text())["questions"]


def routes_of(topology):
    out = {}
    for name, entity in topology.items():
        if entity.get("represented_as") != "edge":
            continue
        props = [p for p in entity.get("properties", {}) if p not in EDGE_FIXED]
        out[name] = {"id": name, "source": entity["source"], "target": entity["target"], "description": entity.get("description", ""), "properties": props}
    return out


def card_sql(card):
    table, where, title, details, *_ = CARDS[card]
    cols = ", ".join(["id", f"{ident(title)} AS title", *(f"{ident(c)} AS {ident(c)}" for c in details)])
    return f"SELECT {cols} FROM {ident(table)}" + (f" WHERE {where}" if where else ""), table, where


def overview(db, topology):
    routes = routes_of(topology)
    cards = {}
    for card, (table, where, _title, _details, label, description) in CARDS.items():
        if table not in topology:
            continue
        n = rows(db, f"SELECT count(*) n FROM {ident(table)}" + (f" WHERE {where}" if where else ""))[0]["n"]
        cards[card] = {"id": card, "label": label, "description": description, "table": table, "count": n}
    qs = []
    for q in questions():
        unknown = [r for r in q["routes"] if r not in routes]
        qs.append({**q, "cards": [c for c in q["cards"] if c in cards], "routes": [r for r in q["routes"] if r in routes], "missing_routes": unknown})
    return {"questions": qs, "cards": cards, "routes": routes}


def items(db, card, q="", limit=MAX_ITEMS, offset=0):
    if card not in CARDS:
        return None
    base, _table, where = card_sql(card)
    title = CARDS[card][2]
    params = []
    if q:
        base += (" AND " if where else " WHERE ") + f"lower({ident(title)}) LIKE %s"
        params.append("%" + q.lower() + "%")
    total = rows(db, f"SELECT count(*) n FROM ({base}) s", params)[0]["n"]
    got = rows(db, f"{base} ORDER BY {ident(title)}, id LIMIT {int(limit)} OFFSET {int(offset)}", params)
    return {"card": card, "total": total, "items": got}


def _neighbours(db, route, item_id, other_table):
    hops = []
    out = []
    if route["target"] == other_table:
        out.append(("source", "target"))
    if route["source"] == other_table:
        out.append(("target", "source"))
    for here, there in out:
        for r in rows(db, f"SELECT * FROM {ident(route['id'])} WHERE {here}=%s", (item_id,)):
            hops.append((r[there], r, here))
    return hops


def pick(db, topology, question_id, picks):
    routes = routes_of(topology)
    q = next((x for x in questions() if x["id"] == question_id), None)
    if q is None:
        return None
    q_routes = [routes[r] for r in q["routes"] if r in routes]
    picks = [(c, i) for c, i in picks if c in q["cards"] and c in CARDS]
    result = {"question": question_id, "picks": [{"card": c, "id": i} for c, i in picks], "cards": {}, "links": []}
    links = []
    seen_links = set()
    for card in q["cards"]:
        table = CARDS[card][0]
        if table not in topology:
            continue
        base, _t, where = card_sql(card)
        allowed = None
        for pc, pid in picks:
            if pc == card:
                continue
            p_table = CARDS[pc][0]
            fitting = [r for r in q_routes if {r["source"], r["target"]} >= {p_table, table}]
            if not fitting:
                continue
            reach = set()
            for r in fitting:
                for other, row, _end in _neighbours(db, r, pid, table):
                    reach.add(other)
                    key = (r["id"], row["id"])
                    if key not in seen_links:
                        seen_links.add(key)
                        links.append({"route": r["id"], "from": row["source"], "to": row["target"], "from_card": pc if row["source"] == pid else card, "to_card": card if row["target"] != pid else pc,
                                      "properties": {k: row[k] for k in r["properties"] if row.get(k) not in (None, "", [])},
                                      **{k: row.get(k) for k in EVIDENCE}})
            allowed = reach if allowed is None else allowed & reach
        if allowed is None:
            total = rows(db, f"SELECT count(*) n FROM ({base}) s")[0]["n"]
            got = rows(db, f"{base} ORDER BY {ident(CARDS[card][2])}, id LIMIT {MAX_ITEMS}")
            result["cards"][card] = {"filtered": False, "total": total, "items": got}
            continue
        ids = sorted(allowed)
        got = []
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            marks = ",".join(["%s"] * len(chunk))
            got += rows(db, f"{base}{' AND ' if where else ' WHERE '}id IN ({marks})", chunk)
        got.sort(key=lambda r: (str(r["title"] or ""), r["id"]))
        result["cards"][card] = {"filtered": True, "total": len(got), "items": got[:MAX_ITEMS]}
    shown = {card: {r["id"] for r in c["items"]} | {i for pc, i in picks if pc == card} for card, c in result["cards"].items()}
    picked = {i for _c, i in picks}
    def kept(l):
        ends = {l["from"], l["to"]}
        return any(e in picked for e in ends) and all(e in picked or any(e in s for s in shown.values()) for e in ends)
    result["links"] = [l for l in links if kept(l)][:MAX_LINKS]
    result["links_total"] = sum(1 for l in links if kept(l))
    return result
