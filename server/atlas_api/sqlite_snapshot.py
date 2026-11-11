import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Lock

from fastapi import HTTPException

from .import_release import search_record, title_for
from .schema import identifier, ordered_tables, read_schema


def decoded_row(cursor, values):
    row = dict(zip((column[0] for column in cursor.description), values))
    for key, value in row.items():
        if isinstance(value, str) and value.startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                row[key] = parsed
    return row


class Snapshot(sqlite3.Connection):
    def __init__(self, path):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"SQLite snapshot missing: {path}. Build the graph or pass an existing graph.sqlite path.")
        super().__init__(":memory:", check_same_thread=False)
        self.lock = Lock()
        self.row_factory = decoded_row
        try:
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as source:
                source.backup(self)
            self.schema = self.read_topology(path)
            self.provenance = json.loads((path.parent / "provenance.json").read_text()) if (path.parent / "provenance.json").is_file() else None
            self.counts = {}
            titles = {}
            self.execute("CREATE TABLE search_document (entity_type TEXT,id TEXT,title TEXT,names TEXT,body TEXT,url TEXT,PRIMARY KEY(entity_type,id))")
            for name in ordered_tables(self.schema):
                entity = self.schema[name]
                records = self.execute(f"SELECT * FROM {identifier(name)} ORDER BY id").fetchall()
                self.counts[name] = len(records)
                if entity["represented_as"] == "node":
                    titles.update({(name, row["id"]): title_for(row) for row in records})
                else:
                    for end in ("source", "target"):
                        self.execute(f"CREATE INDEX IF NOT EXISTS {identifier('atlas_' + name + '_' + end)} ON {identifier(name)} ({identifier(end)})")
                self.executemany("INSERT INTO search_document VALUES (?,?,?,?,?,?)", (search_record(name, row, entity, titles) for row in records))
            self.execute("CREATE VIRTUAL TABLE search_fts USING fts5(names,body,content='search_document',content_rowid='rowid',tokenize='porter unicode61')")
            self.execute("INSERT INTO search_fts(search_fts) VALUES ('rebuild')")
            self.commit()
            self.execute("PRAGMA query_only=ON")
            self.release = {"id": "local:" + path.parent.name, "mode": "sqlite", "snapshot": str(path), "counts": self.counts, "manifest": None, "imported_at": None}
        except BaseException:
            self.close()
            raise

    def read_topology(self, path):
        schema_path = path.parent / "schema_config.yaml"
        metadata = read_schema(schema_path) if schema_path.is_file() else {}
        schema = {}
        for table in self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
            name = table["name"]
            columns = self.execute(f"PRAGMA table_info({identifier(name)})").fetchall()
            endpoints = {row["from"]: row["table"] for row in self.execute(f"PRAGMA foreign_key_list({identifier(name)})") if row["from"] in ("source", "target")}
            is_edge = {"source", "target"}.issubset(endpoints)
            schema[name] = metadata.get(name, {
                "description": "", "represented_as": "edge" if is_edge else "node", **endpoints,
                "properties": {column["name"]: {"INTEGER": "int", "REAL": "float"}.get(column["type"], "str") for column in columns if column["name"] not in {"id", *endpoints}},
                "biotope": {"property_descriptions": {}},
            })
            schema[name].setdefault("description", "")
            schema[name].setdefault("biotope", {}).setdefault("property_descriptions", {})
        return schema

    def record(self, type, id):
        if type not in self.schema:
            raise HTTPException(404, "Unknown record type")
        row = self.execute(f"SELECT * FROM {identifier(type)} WHERE id=?", (id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Record not found")
        entity = self.schema[type]
        for field, kind in entity["properties"].items():
            if kind == "bool" and row[field] is not None:
                row[field] = bool(row[field])
        title = self.execute("SELECT title FROM search_document WHERE entity_type=? AND id=?", (type, id)).fetchone()["title"]
        provenance = {"mappings": [], "evidence": [], "available": self.provenance is not None}
        if self.provenance is not None:
            entry = self.provenance["records"][row["biotope_provenance_id"]]
            provenance["mappings"] = entry["mappings"]
            for index in entry["evidence"]:
                evidence = self.provenance["evidence"][index]
                provenance["evidence"].append({**self.provenance["sources"][evidence["source"]], **{key: value for key, value in evidence.items() if key != "source"}})
        return {"entity_type": type, "title": title, "record": row, "definition": entity, "provenance": provenance}

    def relations(self, type, id, limit, offset):
        if type not in self.schema:
            raise HTTPException(404, "Unknown record type")
        queries, params = [], []
        for name, edge in self.schema.items():
            if edge["represented_as"] != "edge":
                continue
            for endpoint, other in (("source", "target"), ("target", "source")):
                if edge[endpoint] == type:
                    queries.append(f"""SELECT ? relation_type,r.id relation_id,? direction,? entity_type,r.{identifier(other)} id,s.title
                        FROM {identifier(name)} r JOIN search_document s ON s.entity_type=? AND s.id=r.{identifier(other)} WHERE r.{identifier(endpoint)}=?""")
                    params.extend([name, "outgoing" if endpoint == "source" else "incoming", edge[other], edge[other], id])
        if not queries:
            return {"total": 0, "items": [], "limit": limit, "offset": offset}
        union = " UNION ALL ".join(queries)
        total = self.execute(f"SELECT count(*) total FROM ({union})", params).fetchone()["total"]
        items = self.execute(f"SELECT * FROM ({union}) ORDER BY relation_type,title,relation_id,direction LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def search(self, term, type, limit, offset):
        tokens = re.findall(r'"([^\"]+)"|(\w+)', term, re.UNICODE)
        match = " AND ".join('"' + (phrase or word).replace('"', '""') + '"' for phrase, word in tokens)
        if not match:
            return {"query": term, "total": 0, "facets": [], "hits": [], "limit": limit, "offset": offset}
        facets = self.execute("""SELECT d.entity_type,count(*) count FROM search_fts f
            JOIN search_document d ON d.rowid=f.rowid WHERE search_fts MATCH ? GROUP BY d.entity_type ORDER BY count DESC,d.entity_type""", (match,)).fetchall()
        hits = self.execute("""SELECT d.entity_type,d.id,d.title,substr(d.body,1,320) excerpt,d.url,
            -bm25(search_fts,5,1) + CASE WHEN lower(d.title)=lower(?) THEN 10 ELSE 0 END score
            FROM search_fts f JOIN search_document d ON d.rowid=f.rowid WHERE search_fts MATCH ? AND (? IS NULL OR d.entity_type=?)
            ORDER BY score DESC,d.title,d.entity_type,d.id LIMIT ? OFFSET ?""", (term, match, type, type, limit, offset)).fetchall()
        total = sum(facet["count"] for facet in facets if type is None or facet["entity_type"] == type)
        return {"query": term, "total": total, "facets": facets, "hits": hits, "limit": limit, "offset": offset}

    def overlap(self, kinds, groups_only, minimum):
        placeholders = ",".join("?" for _ in kinds)
        holders = self.execute(f"""SELECT id,name,count(DISTINCT initiative) places,
            group_concat(kind || '|' || initiative || '|' || initiative_name,'§') detail
            FROM (SELECT DISTINCT p.id,p.name,h.role_kind kind,i.id initiative,i.name initiative_name
                FROM HoldsRole h JOIN Person p ON p.id=h.source JOIN Initiative i ON i.id=h.target
                WHERE h.role_kind IN ({placeholders}) AND (NOT ? OR i.family='group') ORDER BY i.name,h.role_kind)
            GROUP BY id,name HAVING count(DISTINCT initiative)>=? ORDER BY places DESC,name,id""", [*kinds, groups_only, minimum]).fetchall()
        pairs = self.execute(f"""SELECT first,first_name,second,second_name,count(DISTINCT person) shared,group_concat(DISTINCT name) people
            FROM (SELECT a.target first,ia.name first_name,b.target second,ib.name second_name,a.source person,p.name
                FROM HoldsRole a JOIN HoldsRole b ON a.source=b.source AND a.target<b.target
                JOIN Initiative ia ON ia.id=a.target JOIN Initiative ib ON ib.id=b.target JOIN Person p ON p.id=a.source
                WHERE a.role_kind IN ({placeholders}) AND b.role_kind IN ({placeholders}) AND ia.family='group' AND ib.family='group' ORDER BY p.name)
            GROUP BY first,first_name,second,second_name HAVING count(DISTINCT person)>1
            ORDER BY shared DESC,first_name,first,second LIMIT 60""", [*kinds, *kinds]).fetchall()
        return {"holders": holders, "pairs": pairs}
