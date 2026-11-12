import re

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
