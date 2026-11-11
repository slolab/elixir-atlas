from .sqlite_snapshot import Snapshot


def rows(connection, query, params=()):
    if isinstance(connection, Snapshot):
        query = query.replace("%s", "?")
    return connection.execute(query, params).fetchall()


def one(connection, query, params=()):
    if isinstance(connection, Snapshot):
        query = query.replace("%s", "?")
    return connection.execute(query, params).fetchone()


def home(connection):
    return {
        "kinds": rows(connection, "SELECT kind, count(*) n FROM Initiative GROUP BY kind ORDER BY n DESC, kind"),
        "nodes": rows(connection, """SELECT n.id, n.name,
            (SELECT count(DISTINCT target) FROM TakesPartIn WHERE source=n.id) initiatives,
            (SELECT count(DISTINCT source) FROM InNode WHERE target=n.id) people
            FROM ElixirNode n ORDER BY initiatives DESC, n.name"""),
        "reviews": review_kinds(connection),
        "projects": rows(connection, """SELECT id, name, kind, start, "end" FROM Initiative
            WHERE kind IN ('commissioned_service','implementation_study','eu_project','programme_project','staff_exchange')
            AND start IS NOT NULL AND "end" IS NOT NULL ORDER BY id"""),
    }


def person(connection, id):
    person = one(connection, "SELECT * FROM Person WHERE id=%s", (id,))
    if person is None:
        return None
    return {
        "person": person,
        "nodes": rows(connection, "SELECT n.id,n.name FROM InNode i JOIN ElixirNode n ON n.id=i.target WHERE i.source=%s GROUP BY n.id ORDER BY n.name", (id,)),
        "roles": rows(connection, "SELECT h.*,i.name initiative,i.kind FROM HoldsRole h JOIN Initiative i ON i.id=h.target WHERE h.source=%s ORDER BY i.family,i.name,h.role_kind,h.id", (id,)),
        "led": rows(connection, """SELECT DISTINCT p.id,p.code,p.label,p.kind,p.date,p.status,i.id initiative,i.name initiative_name
            FROM LeadsPlanItem l JOIN PlanItem p ON p.id=l.target JOIN PlanItemOf o ON o.source=p.id JOIN Initiative i ON i.id=o.target
            WHERE l.source=%s ORDER BY p.date NULLS LAST,p.id""", (id,)),
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
        "initiatives": rows(connection, """SELECT i.id,i.name,i.kind,i.family,i.start,i."end" FROM TakesPartIn t JOIN Initiative i ON i.id=t.target
            WHERE t.source=%s GROUP BY i.id ORDER BY i.family,i.kind,i.name""", (id,)),
        "people": rows(connection, """SELECT p.id,p.name,
            (SELECT count(DISTINCT target) FROM HoldsRole WHERE source=p.id) places,
            (SELECT count(DISTINCT target) FROM HoldsRole WHERE source=p.id AND role_kind IN ('lead','co_lead','chair','coordinator','work_package_lead','task_lead')) leads
            FROM InNode n JOIN Person p ON p.id=n.source WHERE n.target=%s GROUP BY p.id ORDER BY leads DESC,places DESC,p.name""", (id,)),
        "tools": one(connection, "SELECT count(DISTINCT source) n FROM ToolInNode WHERE target=%s", (id,))["n"],
        "events": one(connection, "SELECT count(DISTINCT source) n FROM EventInNode WHERE target=%s", (id,))["n"],
        "materials": one(connection, "SELECT count(DISTINCT source) n FROM MaterialInNode WHERE target=%s", (id,))["n"],
    }


def initiative(connection, id):
    initiative = one(connection, "SELECT * FROM Initiative WHERE id=%s", (id,))
    if initiative is None:
        return None
    return {
        "initiative": initiative,
        "plan": rows(connection, "SELECT p.* FROM PlanItemOf o JOIN PlanItem p ON p.id=o.source WHERE o.target=%s ORDER BY p.date NULLS LAST,p.code,p.label,p.id", (id,)),
        "leads": rows(connection, "SELECT l.target plan,pe.id,pe.name FROM LeadsPlanItem l JOIN Person pe ON pe.id=l.source JOIN PlanItemOf o ON o.source=l.target WHERE o.target=%s GROUP BY l.target,pe.id ORDER BY pe.name", (id,)),
        "delivered": rows(connection, "SELECT d.target plan,o.id,o.title,o.url FROM Delivers d JOIN Output o ON o.id=d.source JOIN PlanItemOf p ON p.source=d.target WHERE p.target=%s ORDER BY o.id", (id,)),
        "roles": rows(connection, "SELECT h.source person,p.name,h.role_kind,h.role,h.work_item,h.funding,h.source_url,h.retrieved_at FROM HoldsRole h JOIN Person p ON p.id=h.source WHERE h.target=%s ORDER BY p.name,h.id", (id,)),
        "nodes": rows(connection, "SELECT n.id,n.name,count(DISTINCT t.source_url) sources FROM TakesPartIn t JOIN ElixirNode n ON n.id=t.source WHERE t.target=%s GROUP BY n.id ORDER BY n.name", (id,)),
        "outputs": rows(connection, "SELECT o.*,f.basis FROM OutputOf f JOIN Output o ON o.id=f.source WHERE f.target=%s ORDER BY o.date DESC NULLS LAST,o.id", (id,)),
        "related": rows(connection, """SELECT i.id,i.name,i.kind,count(*) n FROM RelatedTo r
            JOIN Initiative i ON i.id=CASE WHEN r.source=%s THEN r.target ELSE r.source END
            WHERE (r.source=%s OR r.target=%s) AND i.id!=%s GROUP BY i.id ORDER BY n DESC,i.name""", (id,id,id,id)),
        "statements": rows(connection, "SELECT s.* FROM StatementAbout a JOIN SourceStatement s ON s.id=a.source WHERE a.target=%s ORDER BY s.coverage,s.source_url,s.id", (id,)),
        "topics": rows(connection, "SELECT t.label FROM InitiativeTopic it JOIN Topic t ON t.id=it.target WHERE it.source=%s GROUP BY t.id ORDER BY count(*) DESC,t.label", (id,)),
        "tools": rows(connection, "SELECT t.id,t.name,t.url FROM ToolFor f JOIN Tool t ON t.id=f.source WHERE f.target=%s GROUP BY t.id ORDER BY t.name", (id,)),
        "events": rows(connection, "SELECT e.id,e.title,e.url,e.start FROM EventFor f JOIN TrainingEvent e ON e.id=f.source WHERE f.target=%s GROUP BY e.id ORDER BY e.start DESC NULLS LAST,e.id", (id,)),
        "materials": rows(connection, "SELECT m.id,m.title,m.url,m.date_published FROM MaterialFor f JOIN TrainingMaterial m ON m.id=f.source WHERE f.target=%s GROUP BY m.id ORDER BY m.date_published DESC NULLS LAST,m.id", (id,)),
        "reviews": subject_reviews(connection, id),
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


def overlap(connection, liaisons, groups_only, minimum):
    kinds = ["lead", "co_lead", "chair", "coordinator", "deputy", "work_package_lead", "task_lead"] + (["liaison"] if liaisons else [])
    if isinstance(connection, Snapshot):
        return connection.overlap(kinds, groups_only, minimum)
    return {
        "holders": rows(connection, """SELECT id,name,count(DISTINCT initiative) places,
            string_agg(kind || '|' || initiative || '|' || initiative_name,'§' ORDER BY initiative_name,kind) detail
            FROM (SELECT DISTINCT p.id,p.name,h.role_kind kind,i.id initiative,i.name initiative_name
                FROM HoldsRole h JOIN Person p ON p.id=h.source JOIN Initiative i ON i.id=h.target
                WHERE h.role_kind=ANY(%s) AND (NOT %s OR i.family='group')) roles
            GROUP BY id,name HAVING count(DISTINCT initiative)>=%s ORDER BY places DESC,name,id""", (kinds,groups_only,minimum)),
        "pairs": rows(connection, """SELECT a.target "first",ia.name first_name,b.target "second",ib.name second_name,
            count(DISTINCT a.source) shared,string_agg(DISTINCT p.name,',' ORDER BY p.name) people
            FROM HoldsRole a JOIN HoldsRole b ON a.source=b.source AND a.target<b.target
            JOIN Initiative ia ON ia.id=a.target JOIN Initiative ib ON ib.id=b.target JOIN Person p ON p.id=a.source
            WHERE a.role_kind=ANY(%s) AND b.role_kind=ANY(%s) AND ia.family='group' AND ib.family='group'
            GROUP BY a.target,ia.name,b.target,ib.name HAVING count(DISTINCT a.source)>1 ORDER BY shared DESC,ia.name,a.target,b.target LIMIT 60""", (kinds,kinds)),
    }
