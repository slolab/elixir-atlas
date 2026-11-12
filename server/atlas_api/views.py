import re

from fastapi import HTTPException

from .sqlite_snapshot import Snapshot


def dialect(connection, query):
    if not isinstance(connection, Snapshot):
        return query
    query = re.sub(r"string_agg\(DISTINCT ([^,()]+), ', '\)", r"group_concat(DISTINCT \1)", query)
    return query.replace("string_agg(", "group_concat(").replace("%s", "?")


def rows(connection, query, params=()):
    return connection.execute(dialect(connection, query), params).fetchall()


def one(connection, query, params=()):
    return connection.execute(dialect(connection, query), params).fetchone()


def home(connection):
    return {
        "kinds": rows(connection, "SELECT kind, count(*) n FROM Initiative GROUP BY kind ORDER BY n DESC, kind"),
        "nodes": rows(connection, """SELECT n.id, n.name,
            (SELECT count(DISTINCT target) FROM TakesPartIn WHERE source=n.id) initiatives,
            (SELECT count(DISTINCT source) FROM InNode WHERE target=n.id) people
            FROM ElixirNode n ORDER BY initiatives DESC, n.name"""),
        "reviews": review_kinds(connection),
        "projects": rows(connection, """SELECT id, name, kind, start, "end" FROM Initiative
            WHERE kind IN ('commissioned_service','eu_project','staff_exchange')
            AND start IS NOT NULL AND "end" IS NOT NULL ORDER BY id"""),
    }


def person(connection, id):
    person = one(connection, "SELECT * FROM Person WHERE id=%s", (id,))
    if person is None:
        return None
    return {
        "person": person,
        "same_name_records": [row["id"] for row in rows(connection, "SELECT id FROM Person WHERE name=%s AND id!=%s ORDER BY id", (person["name"], id))],
        "nodes": rows(connection, "SELECT n.id,n.name FROM InNode i JOIN ElixirNode n ON n.id=i.target WHERE i.source=%s GROUP BY n.id ORDER BY n.name", (id,)),
        "involved_in": rows(connection, """SELECT i.id,i.name,i.kind,i.status,i.period_status,v.leadership,v.roles,v.plan_items,v.outputs,v.tools,v.bases
            FROM InvolvedIn v JOIN Initiative i ON i.id=v.target WHERE v.source=%s ORDER BY v.leadership DESC,i.kind,i.name""", (id,)),
        "roles": rows(connection, "SELECT h.*,i.name initiative,i.kind FROM HoldsRole h JOIN Initiative i ON i.id=h.target WHERE h.source=%s ORDER BY i.family,i.name,h.role_kind,h.id", (id,)),
        "led": rows(connection, """SELECT DISTINCT p.id,p.code,p.label,p.kind,p.date,p.status,i.id initiative,i.name initiative_name
            FROM WorksOnPlanItem l JOIN PlanItem p ON p.id=l.target JOIN PlanItemOf o ON o.source=p.id JOIN Initiative i ON i.id=o.target
            WHERE l.source=%s AND l.role='lead' ORDER BY p.date NULLS LAST,p.id""", (id,)),
        "outputs": rows(connection, "SELECT o.id,o.title,o.url,o.date FROM Authored a JOIN Output o ON o.id=a.target WHERE a.source=%s GROUP BY o.id ORDER BY o.date DESC NULLS LAST,o.id", (id,)),
        "tools": rows(connection, "SELECT t.id,t.name,t.url FROM CreditedForTool c JOIN Tool t ON t.id=c.target WHERE c.source=%s GROUP BY t.id ORDER BY t.name", (id,)),
        "organisations": rows(connection, "SELECT g.name FROM AffiliatedWith a JOIN Organisation g ON g.id=a.target WHERE a.source=%s GROUP BY g.id ORDER BY g.name", (id,)),
        "reviews": subject_reviews(connection, id),
    }


def node(connection, id):
    node = one(connection, "SELECT * FROM ElixirNode WHERE id=%s", (id,))
    if node is None:
        return None
    return {
        "node": node,
        "portfolio": rows(connection, """SELECT i.id,i.name,i.kind,i.status,v.period,v.period_status,v.bases,v.listed_on_own_page,v.beneficiaries,v.people,v.sources
            FROM NodeInvolvedIn v JOIN Initiative i ON i.id=v.target WHERE v.source=%s ORDER BY i.family,i.kind,i.name""", (id,)),
        "initiatives": rows(connection, """SELECT i.id,i.name,i.kind,i.family,i.start,i."end" FROM TakesPartIn t JOIN Initiative i ON i.id=t.target
            WHERE t.source=%s GROUP BY i.id,i.name,i.kind,i.family,i.start,i."end" ORDER BY i.family,i.kind,i.name""", (id,)),
        "people": rows(connection, """SELECT p.id,p.name,
            (SELECT count(DISTINCT target) FROM HoldsRole WHERE source=p.id) places,
            (SELECT count(DISTINCT target) FROM HoldsRole WHERE source=p.id AND role_kind IN ('lead','co_lead','chair','coordinator','work_package_lead','task_lead')) leads
            FROM InNode n JOIN Person p ON p.id=n.source WHERE n.target=%s GROUP BY p.id ORDER BY leads DESC,places DESC,p.name""", (id,)),
        "tools": one(connection, "SELECT count(DISTINCT source) n FROM ToolInNode WHERE target=%s", (id,))["n"],
        "events": one(connection, "SELECT count(DISTINCT source) n FROM EventInNode WHERE target=%s", (id,))["n"],
        "materials": one(connection, "SELECT count(DISTINCT source) n FROM MaterialInNode WHERE target=%s", (id,))["n"],
    }


def initiative(connection, id):
    item = one(connection, "SELECT * FROM Initiative WHERE id=%s", (id,))
    if item is None:
        return None
    item = {key: value for key, value in item.items() if key != "scope"}
    return {
        "initiative": item,
        "people": rows(connection, """SELECT p.id,p.name,v.leadership,v.roles,v.plan_items,v.outputs,v.tools,v.nodes,v.organisations,v.bases,v.source_urls
            FROM InvolvedIn v JOIN Person p ON p.id=v.source WHERE v.target=%s ORDER BY v.leadership DESC,p.name""", (id,)),
        "node_involvement": rows(connection, """SELECT n.id,n.name,v.bases,v.listed_on_own_page,v.beneficiaries,v.people,v.sources FROM NodeInvolvedIn v
            JOIN ElixirNode n ON n.id=v.source WHERE v.target=%s ORDER BY v.listed_on_own_page DESC,n.name""", (id,)),
        "nodes": rows(connection, """SELECT n.id,n.name,count(DISTINCT t.source_url) sources,string_agg(DISTINCT t.basis, ', ') basis FROM TakesPartIn t
            JOIN ElixirNode n ON n.id=t.source WHERE t.target=%s GROUP BY n.id,n.name ORDER BY n.name""", (id,)),
        "shares_work_with": rows(connection, """SELECT i.id,i.name,i.kind,i.status,count(*) items,string_agg(w.via || ': ' || w.item, ' | ') shared
            FROM SharesWorkWith w JOIN Initiative i ON i.id=w.target WHERE w.source=%s GROUP BY i.id,i.name,i.kind,i.status ORDER BY items DESC,i.name""", (id,)),
        "plan_links": rows(connection, """SELECT i.id,i.name,i.kind,l.direction,l.item,l.linked_item,l.relation,l.quote,l.source_url
            FROM PlanLinkedTo l JOIN Initiative i ON i.id=l.target WHERE l.source=%s ORDER BY i.name,l.item,l.linked_item""", (id,)),
        "related": rows(connection, """SELECT i.id,i.name,i.kind,i.status,i.period_status,count(*) n,max(r.quote) quote FROM RelatedTo r JOIN Initiative i ON i.id=r.target
            WHERE r.source=%s AND i.id!=%s GROUP BY i.id,i.name,i.kind,i.status,i.period_status ORDER BY n DESC,i.name""", (id, id)),
        "became": rows(connection, """SELECT b.source,s.name source_name,b.target,t.name target_name,b.date,b.evidence,b.source_url FROM Became b
            JOIN Initiative s ON s.id=b.source JOIN Initiative t ON t.id=b.target WHERE b.source=%s OR b.target=%s""", (id, id)),
        "reviews": subject_reviews(connection, id),
        "beneficiaries": rows(connection, """SELECT g.id,g.name,g.country,p.participation,p.net_eu_contribution_eur,p.total_cost_eur,p.source_url
            FROM ParticipatesIn p JOIN Organisation g ON g.id=p.source WHERE p.target=%s ORDER BY p.net_eu_contribution_eur DESC NULLS LAST,g.name""", (id,)),
        "resources": rows(connection, """SELECT r.id,r.name,r.kind,c.basis,c.purpose,c.url,c.source_url,
            (SELECT string_agg(target, ', ') FROM IsTool WHERE source=r.id) tools
            FROM Recommends c JOIN Resource r ON r.id=c.target WHERE c.source=%s ORDER BY r.name,c.source_url""", (id,)),
        "tools": rows(connection, """SELECT t.id,t.name,t.url,string_agg(DISTINCT f.basis, ', ') basis,t.recommended_by FROM ToolFor f JOIN Tool t ON t.id=f.source
            WHERE f.target=%s GROUP BY t.id,t.name,t.url,t.recommended_by ORDER BY t.name""", (id,)),
        "outputs": rows(connection, "SELECT o.*,f.basis FROM OutputOf f JOIN Output o ON o.id=f.source WHERE f.target=%s ORDER BY o.date DESC NULLS LAST,o.id", (id,)),
        "events": rows(connection, """SELECT e.id,e.title,e.url,e.start,e.listed_in,string_agg(DISTINCT f.basis, ', ') basis,max(f.collection) collection
            FROM EventFor f JOIN Event e ON e.id=f.source WHERE f.target=%s GROUP BY e.id,e.title,e.url,e.start,e.listed_in
            ORDER BY e.start DESC NULLS LAST,e.id""", (id,)),
        "materials": rows(connection, """SELECT m.id,m.title,m.url,m.date_published,max(f.collection) collection FROM MaterialFor f
            JOIN TrainingMaterial m ON m.id=f.source WHERE f.target=%s GROUP BY m.id,m.title,m.url,m.date_published
            ORDER BY m.date_published DESC NULLS LAST,m.id""", (id,)),
        "topics": rows(connection, "SELECT t.label FROM InitiativeTopic it JOIN Topic t ON t.id=it.target WHERE it.source=%s GROUP BY t.id,t.label ORDER BY count(*) DESC,t.label", (id,)),
        "roles": rows(connection, "SELECT h.source person,p.name,h.role_kind,h.role,h.work_item,h.funding,h.source_url,h.retrieved_at FROM HoldsRole h JOIN Person p ON p.id=h.source WHERE h.target=%s ORDER BY p.name,h.id", (id,)),
        "leads": rows(connection, "SELECT l.target plan,pe.id,pe.name FROM WorksOnPlanItem l JOIN Person pe ON pe.id=l.source JOIN PlanItemOf o ON o.source=l.target WHERE o.target=%s AND l.role='lead' GROUP BY l.target,pe.id,pe.name ORDER BY pe.name", (id,)),
        "delivered": rows(connection, "SELECT d.target plan,o.id,o.title,o.url FROM Delivers d JOIN Output o ON o.id=d.source JOIN PlanItemOf p ON p.source=d.target WHERE p.target=%s ORDER BY o.id", (id,)),
        "statements": rows(connection, "SELECT s.* FROM StatementAbout a JOIN SourceStatement s ON s.id=a.source WHERE a.target=%s ORDER BY s.coverage,s.source_url,s.id", (id,)),
        "plan": rows(connection, "SELECT p.* FROM PlanItemOf o JOIN PlanItem p ON p.id=o.source WHERE o.target=%s ORDER BY p.date NULLS LAST,p.code,p.label,p.id", (id,)),
    }


def kind(connection, id):
    return rows(connection, """SELECT i.id,i.name,i.start,i."end",
        (SELECT count(DISTINCT source) FROM HoldsRole WHERE target=i.id) people,
        (SELECT count(DISTINCT source) FROM TakesPartIn WHERE target=i.id) nodes,
        (SELECT count(*) FROM PlanItemOf WHERE target=i.id) plan
        FROM Initiative i WHERE i.kind=%s ORDER BY i.name,i.id""", (id,))


def review_kinds(connection):
    return rows(connection, "SELECT kind,count(*) n FROM ReviewItem WHERE status='open' GROUP BY kind ORDER BY n DESC,kind")


def subject_reviews(connection, id):
    if isinstance(connection, Snapshot):
        return rows(connection, "SELECT * FROM ReviewItem WHERE status='open' AND EXISTS (SELECT 1 FROM json_each(subjects) WHERE value=%s) ORDER BY id", (id,))
    return rows(connection, "SELECT * FROM ReviewItem WHERE status='open' AND subjects @> ARRAY[%s] ORDER BY id", (id,))


def reviews(connection, kind):
    kinds = review_kinds(connection)
    active = kind or next(iter(kinds), {}).get("kind", "")
    return {"kinds": kinds, "active": active, "items": rows(connection, "SELECT * FROM ReviewItem WHERE status='open' AND kind=%s ORDER BY property,question,id", (active,))}


DIRECTORY = "(i.kind IN ('community','platform','focus_group') AND i.status='current')"


def overlap(connection, liaisons, groups_only, minimum, directory):
    kinds = ["lead", "co_lead", "chair", "coordinator", "deputy", "work_package_lead", "task_lead"] + (["liaison"] if liaisons else [])
    if isinstance(connection, Snapshot):
        return connection.overlap(kinds, groups_only, minimum, directory)
    return {
        "holders": rows(connection, """SELECT id,name,count(DISTINCT initiative) places,
            string_agg(kind || '|' || initiative || '|' || initiative_name,'§' ORDER BY initiative_name,kind) detail
            FROM (SELECT DISTINCT p.id,p.name,h.role_kind kind,i.id initiative,i.name initiative_name
                FROM HoldsRole h JOIN Person p ON p.id=h.source JOIN Initiative i ON i.id=h.target
                WHERE h.role_kind=ANY(%s) AND (NOT %s OR i.family='group') AND (NOT %s OR {DIRECTORY})) roles
            GROUP BY id,name HAVING count(DISTINCT initiative)>=%s ORDER BY places DESC,name,id""".replace("{DIRECTORY}", DIRECTORY), (kinds,groups_only,directory,minimum)),
        "pairs": rows(connection, """SELECT a.target "first",ia.name first_name,b.target "second",ib.name second_name,
            count(DISTINCT a.source) shared,string_agg(DISTINCT p.name,',' ORDER BY p.name) people
            FROM HoldsRole a JOIN HoldsRole b ON a.source=b.source AND a.target<b.target
            JOIN Initiative ia ON ia.id=a.target JOIN Initiative ib ON ib.id=b.target JOIN Person p ON p.id=a.source
            WHERE a.role_kind=ANY(%s) AND b.role_kind=ANY(%s) AND ia.family='group' AND ib.family='group'
            AND (NOT %s OR {A}) AND (NOT %s OR {B})
            GROUP BY a.target,ia.name,b.target,ib.name HAVING count(DISTINCT a.source)>1 ORDER BY shared DESC,ia.name,a.target,b.target LIMIT 60""".replace("{A}", DIRECTORY.replace("i.", "ia.")).replace("{B}", DIRECTORY.replace("i.", "ib.")), (kinds,kinds,directory,directory)),
    }


LEAD_ROLES = ("lead", "co_lead", "chair", "contact", "coordinator")


def topics(connection):
    return rows(connection, """WITH community_topics AS (
        SELECT i.source community, i.target topic FROM InitiativeTopic i JOIN Initiative g ON g.id=i.source WHERE g.kind='community'
        UNION
        SELECT f.target community, x.target topic FROM ToolTopic x JOIN ToolFor f ON f.source=x.source
        JOIN Initiative g ON g.id=f.target WHERE g.kind='community'
        ) SELECT t.id, t.label,
        (SELECT count(*) FROM community_topics c WHERE c.topic=t.id) communities,
        (SELECT count(DISTINCT x.source) FROM ToolTopic x WHERE x.target=t.id) tools,
        (SELECT count(DISTINCT x.source) FROM MaterialTopic x WHERE x.target=t.id) materials
        FROM Topic t ORDER BY t.label""")


def marks(values):
    return ",".join(["%s"] * len(values))


def topic_support(connection, topic_ids, today):
    if isinstance(connection, Snapshot) and not {"Resource", "Recommends", "IsTool", "Event"}.issubset(connection.schema):
        raise HTTPException(409, "Find by topic needs a newer Atlas snapshot. Restart the dashboard with the 20261112 release or a newer build.")
    chosen = rows(connection, f"SELECT id, label FROM Topic WHERE id IN ({marks(topic_ids)}) ORDER BY label", topic_ids)
    ids = [t["id"] for t in chosen]
    if len(ids) != len(topic_ids):
        raise HTTPException(422, "A selected research topic is not in this snapshot. Remove it and choose another topic.")
    by_topic = rows(connection, f"""SELECT g.id, g.name, t.label topic, i.evidence, i.source_url, i.retrieved_at
        FROM InitiativeTopic i JOIN Initiative g ON g.id=i.source JOIN Topic t ON t.id=i.target
        WHERE g.kind='community' AND i.target IN ({marks(ids)}) ORDER BY g.name, t.label""", ids)
    by_tools = rows(connection, f"""SELECT g.id, g.name, count(DISTINCT f.source) tools
        FROM ToolTopic x JOIN ToolFor f ON f.source=x.source JOIN Initiative g ON g.id=f.target
        WHERE g.kind='community' AND x.target IN ({marks(ids)}) GROUP BY g.id, g.name""", ids)
    communities = {}
    for row in by_topic:
        entry = communities.setdefault(row["id"], {"id": row["id"], "name": row["name"], "topics": [], "tools": 0})
        if row["topic"] not in [t["label"] for t in entry["topics"]]:
            entry["topics"].append({"label": row["topic"], "evidence": row["evidence"], "source_url": row["source_url"], "retrieved_at": row["retrieved_at"]})
    for row in by_tools:
        communities.setdefault(row["id"], {"id": row["id"], "name": row["name"], "topics": [], "tools": 0})["tools"] = row["tools"]
    community_ids = list(communities)
    if community_ids:
        for row in rows(connection, f"SELECT id, contacts, join_url, joining, pages FROM Initiative WHERE id IN ({marks(community_ids)})", community_ids):
            communities[row["id"]].update(contacts=row["contacts"], join_url=row["join_url"], joining=row["joining"], page=(row["pages"] or [None])[0])
        leads = rows(connection, f"""SELECT h.target community, p.id, p.name, string_agg(DISTINCT h.role_kind, ', ') roles
            FROM HoldsRole h JOIN Person p ON p.id=h.source
            WHERE h.target IN ({marks(community_ids)}) AND h.role_kind IN ({marks(LEAD_ROLES)})
            GROUP BY h.target, p.id, p.name ORDER BY p.name""", community_ids + list(LEAD_ROLES))
        for row in leads:
            communities[row["community"]].setdefault("leads", []).append({"id": row["id"], "name": row["name"], "roles": row["roles"]})
    ranked = sorted(communities.values(), key=lambda c: (-len(c["topics"]), -c["tools"], c["name"]))
    names = {c["id"]: c["name"] for c in ranked}
    resources = {}
    core = [c["id"] for c in ranked if c["topics"]] or community_ids
    if core:
        for row in rows(connection, f"""SELECT r.id, r.name, r.kind, r.url, e.source community, e.basis, e.purpose, e.evidence, e.source_url,
                (SELECT t.homepage FROM IsTool s JOIN Tool t ON t.id=s.target WHERE s.source=r.id LIMIT 1) homepage
                FROM Recommends e JOIN Resource r ON r.id=e.target WHERE e.source IN ({marks(core)}) ORDER BY r.name""", core):
            entry = resources.setdefault(row["id"], {"id": row["id"], "name": row["name"], "kind": row["kind"], "url": row["url"] or row["homepage"], "by": []})
            if not any(b["community"] == names[row["community"]] and b["basis"] == row["basis"] for b in entry["by"]):
                entry["by"].append({"community": names[row["community"]], "basis": row["basis"], "purpose": row["purpose"], "evidence": row["evidence"], "source_url": row["source_url"]})
    covered = {row["target"] for row in rows(connection, f"SELECT target FROM IsTool WHERE source IN ({marks(list(resources))})", list(resources))} if resources else set()
    tools = rows(connection, f"""SELECT t.id, t.name, t.homepage, t.url, t.tool_types, string_agg(DISTINCT g.name, ', ') listed_for
        FROM ToolTopic x JOIN Tool t ON t.id=x.source
        LEFT JOIN ToolFor f ON f.source=t.id LEFT JOIN Initiative g ON g.id=f.target AND g.kind='community'
        WHERE x.target IN ({marks(ids)}) GROUP BY t.id, t.name, t.homepage, t.url, t.tool_types ORDER BY t.name""", ids)
    tools = sorted((t for t in tools if t["id"] not in covered), key=lambda t: (not t["listed_for"], t["name"].lower()))
    papers = rows(connection, f"""SELECT DISTINCT o.id, o.title, o.date, o.url, o.doi, o.kind, o.resource_type, g.name community
        FROM OutputOf l JOIN Output o ON o.id=l.source JOIN Initiative g ON g.id=l.target
        WHERE l.target IN ({marks(community_ids)}) AND (o.kind IN ('article','document') OR o.resource_type IN ('Report','Publication','Journal article','Preprint','Conference paper'))
        ORDER BY o.date DESC NULLS LAST, o.title, g.name""", community_ids) if community_ids else []
    materials = rows(connection, f"""SELECT DISTINCT m.id, m.title, m.url, m.date_published, m.content_provider
        FROM MaterialTopic x JOIN TrainingMaterial m ON m.id=x.source WHERE x.target IN ({marks(ids)})
        ORDER BY m.date_published DESC NULLS LAST, m.title""", ids)
    events = rows(connection, f"""SELECT DISTINCT e.id, e.title, e.url, e.start, e."end", e.city, e.country, e.online
        FROM EventTopic x JOIN Event e ON e.id=x.source WHERE x.target IN ({marks(ids)}) AND e.start >= %s
        ORDER BY e.start, e.title""", ids + [today])
    return {"topics": chosen, "communities": ranked, "resources": sorted(resources.values(), key=lambda r: (-len(r["by"]), r["name"].lower())),
            "tools": tools[:60], "tools_total": len(tools), "papers": papers[:30], "papers_total": len(papers),
            "materials": materials[:40], "materials_total": len(materials), "events": events[:40], "events_total": len(events)}
