# Bundled Atlas

The installed skill includes the complete dated release: all graph records, schema descriptions and build provenance. Its compressed assets are unpacked into a temporary cache when needed and checked against release hashes. Python 3 with SQLite is sufficient. Do not install packages or call the live API to answer from this release.

In these examples, replace `<skill directory>` with the directory containing the loaded `SKILL.md`:

```sh
atlas='<skill directory>/scripts/atlas.py'
python3 "$atlas" verify
python3 "$atlas" search metabolomics --type Initiative
python3 "$atlas" record Initiative initiative:metabolomics
python3 "$atlas" schema Initiative InvolvedIn Person
python3 "$atlas" query 'SELECT kind, count(*) AS n FROM Initiative GROUP BY kind ORDER BY n DESC'
```

`verify` checks release hashes, database integrity, record counts and the search index. `release` reports the packaged release and table counts. Every response identifies that release. Data freshness changes only when a new release package is installed; the current date is not the snapshot date.

## Search and records

`search TERM` searches full record text and relationship endpoint names. Use short variants separately. Words and quoted phrases are combined with AND; search uses SQLite FTS5 English stemming, so ranking and matches can differ from the online PostgreSQL API. It does not implement the API's fuzzy matching, `OR` or exclusion syntax. Try alternate spellings explicitly.

Use `--type Initiative` to filter a table, `--limit 30` to set the page size (maximum 100), and `--offset 30` for the next page. `total` and `has_more` describe the filtered results. `facets` count all matching types before the type filter. Excerpts are only the first 320 characters; use `record` or SQL for evidence. Deduplicate by `entity_type` and `id`, and paginate until coverage is complete.

`record TYPE ID` returns every field plus the record's resolved build provenance. Array fields become JSON arrays and boolean fields become booleans. IDs must come from search or query results. A record is one graph row, not the online API's combined initiative, Node or person view: follow relationships with SQL as below.

## Schema and SQL

`schema` lists table descriptions and relationship directions. `schema Initiative InvolvedIn Person` returns their full definitions, including property types, descriptions and nullable fields. `schema --full` returns every definition; select tables instead when this is large.

Use SQLite syntax. Table names are case-insensitive and have no underscores (`InvolvedIn`, not `involved_in`). Every table has an `id`. Relationship tables have `source` and `target`; their definitions name the endpoint tables. Fields described as `str[]` are stored as JSON text, booleans as 0/1, and dates as text with varying precision. Source URLs are in the records, not in a separate remote service.

`query SQL` accepts one read-only statement: joins, CTEs, subqueries, unions, aggregates and window functions work. Use `query -` with a heredoc for complex SQL. Quote identifiers such as `"end"`. Use `json_each` for array membership and `json_extract` for individual elements. There is no PostgreSQL `atlas.` namespace, `ILIKE`, `unnest`, `ANY` or `::` cast syntax.

The response has ordered `columns`, positional `rows`, `row_count`, `truncated` and `truncation_reason`. SQL results retain JSON arrays as text; parse them as JSON when displaying their items. The default limit is 100 rows; `--limit` accepts up to 1,000. Results are capped at 1 MB and queries at five seconds. When truncated, narrow fields, aggregate, or paginate with stable `ORDER BY` and `LIMIT`/`OFFSET`. A SQL `LIMIT` still limits your population even when `truncated` is false. Save large JSON responses to a file and inspect fields rather than cutting the output with `head`.

### People, roles and affiliations for an initiative

```sh
python3 "$atlas" query - --limit 1000 <<'SQL'
SELECT p.id, p.name, i.leadership, i.roles, i.plan_items,
       i.outputs, i.tools, i.nodes, i.organisations, i.source_urls
FROM InvolvedIn i JOIN Person p ON p.id = i.source
WHERE i.target = 'initiative:metabolomics'
ORDER BY p.name, p.id
SQL
```

Add `AND i.leadership = 1` for leadership involvement, which includes chairs, coordinators, deputies, work-package/task leads and plan-item leads as well as co-leads and liaisons. Inspect `roles` or `HoldsRole` for the exact requested role. For a person's involvement, filter `i.source` instead. Query `Person` for identifiers and affiliation details; the group's contact information is in `Initiative.contacts`. `InvolvedIn.tools` includes every bio.tools tool credited to the person; `[this initiative]` marks tools the initiative tags or recommends.

### A Node's portfolio

Resolve the Node's ID first, then join `NodeInvolvedIn n` to `Initiative i ON i.id = n.target`, filtering `n.source`. Select `n.bases`, `n.beneficiaries`, `n.people`, `n.plan_summary`, `n.leads_plan_items`, `n.works_on_plan_items`, `n.node_site` and `n.limits` along with the initiative's kind, dates and `period_status`. An empty lead list with a plan summary means the Node leads none of those plan items. `node_site` says whether the initiative appears on the Node's collected project listing; null is not a confirmed absence.

### Plans, outputs and overlaps

- Plans: join `PlanItemOf e` to `PlanItem p ON p.id = e.source`, filtering `e.target` by initiative. `PlanItem.tools` names tools mentioned in the plan and their credited people. Its `leads` contains real leads; longer source lists can be in `participants`. `WorksOnPlanItem` records a person's role as `lead` or `participant`.
- Outputs: join `OutputOf e` to `Output o ON o.id = e.source`, filtering `e.target`. Check `e.basis`: `description` only mentions the group; other bases include `title`, `named`, `grant`, `linked`, `deliverable`, `author` and `series`. Also search named mentions and related projects when direct links are sparse. `Authored.role` distinguishes creators from contributors.
- Overlaps: query `SharesWorkWith` and `PlanLinkedTo` by `source`; both store both directions. The former records shared projects, outputs, tools, leaders or resources. The latter includes a source quote explicitly relating work items, with `item`, `linked_item` and `source_url`.
- Transitions and related groups: query `Became` and `RelatedTo`. Related links include parent programmes, partners and mentions; they do not by themselves establish joint work.

Read each relationship's schema to confirm endpoints before joining. Count distinct entity IDs when multiple sources describe the same relationship.

## Evidence and scope

- Read `Initiative.leaders`, `limits`, `recent_activity`, `latest_own_activity`, `latest_activity` and `scope` directly. `contacts`, `join_url` and `joining` come from its own ELIXIR page; `pages[0]` is its main page. `programme` describes programme membership, not project kind. `period_status` is assessed at the release snapshot.
- `SourceStatement`, `SourceDocument` and relationship records carry claims, quotes, source URLs and dates. Internal provenance paths are not public citations; cite original URLs or DOIs. `SourceDocument.published` and `modified` are page dates, not necessarily group activity dates.
- `TakesPartIn.basis`: `own_page` is the initiative's current official Node list, `stated` another source, `beneficiary_country` an EU beneficiary's country, and `lead_node` only the Node of a lead. `NodeInvolvedIn.bases` also includes `people`. `ParticipatesIn` holds CORDIS organisations and EU contributions.
- `HoldsRole.role_kind = 'candidate'` identifies election candidates, not office holders. `work_item` names the work package, task or governance body. Community membership lists are not public.
- `Recommends` records a resource recommended or developed by the group's own page or paper. `IsTool` connects resources to bio.tools. `ToolFor` is a tag or community-domain listing; it is not endorsement. `Tool.recommended_by` is empty for catalogue-only records.
- `Event` and `TrainingMaterial.collections` name TeSS collections; `collections_unnamed` counts others. Records without a group collection are catalogue-only. `Event.listed_in` identifies TeSS versus the ELIXIR website; `provider_url` is the organiser's page. `EventFor` and `MaterialFor` retain source URLs.
- `ReviewItem` exposes unresolved identities and conflicting values. Topic assignments can be model-derived; TeSS coverage includes non-ELIXIR training and incomplete Node links. Import and retrieval dates are not activity dates.

The public API remains available separately as described in [api.md](api.md). It is optional and can hold a different release. Do not mix releases without explicitly stating that difference.
