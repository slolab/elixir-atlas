# Atlas API

Base URL: `https://atlas-production-d392fb6d.up.railway.app`

Requests return JSON without authentication. URL-encode GET parameters and send SQL as a JSON POST body. Full endpoint details: [API docs](https://atlas-production-d392fb6d.up.railway.app/docs).

## SQL

Check `/api/release`. When `api.sql` is true, use `/api/schema?format=sql&detail=summary` to discover tables and relationship directions. Fetch full definitions with `&tables=initiative,holdsrole,person` (substitute your tables). These definitions retain the build's descriptions, types, nullability and foreign keys. Reuse them during the investigation. The unfiltered `/api/schema?format=sql` still returns everything; save large responses and inspect relevant sections rather than relying on truncated terminal output. Otherwise use the GET routes below.

`POST /api/query` accepts `{"sql":"SELECT ...","limit":1000}`. It supports one read query with joins, CTEs, subqueries, unions, aggregates and window functions. FROM functions require `WITH ORDINALITY`, for example `unnest(i.pages) WITH ORDINALITY AS u(url, position)`. Quote column identifiers, especially reserved words such as `"end"`. Dates may be text with varying precision; read their descriptions before casting. Count distinct entity IDs when several source-specific edges describe the same relationship.

```sh
atlas='https://atlas-production-d392fb6d.up.railway.app'
curl -sS --max-time 15 "$atlas/api/query" \
  -H 'Content-Type: application/json' \
  --data '{"sql":"SELECT kind, count(*) AS n FROM initiative GROUP BY kind ORDER BY n DESC"}'
```

`rows` are positional arrays matching the ordered `columns` names/type OIDs. Responses also identify the release, schema/API revision and request, with row count and duration. Limits are 1,000 returned rows, 1 MB and five seconds. `truncated: true` and `truncation_reason` indicate an API cutoff: narrow the query, aggregate, or paginate with stable `ORDER BY` and `LIMIT`/`OFFSET`. Aggregates use all matching input rows; `truncated: false` does not undo your SQL `LIMIT`.

Errors include a message, SQLSTATE, position and hint where available. Correct the query from that feedback. Timeouts return HTTP 408 with no partial result; oversized results return 422. Retry a transient 503 or network failure once.

## Search and GET routes

| Endpoint | Parameters | Returns |
| --- | --- | --- |
| `/api/search` | `q`, optional `type`, `limit`, `offset` | Ranked `hits`, `total`, type `facets` |
| `/api/record` | `type`, `id` | Full record, definition and provenance |
| `/api/relations` | `type`, `id`, optional `limit`, `offset` | Related records, relationship type/ID, direction and total |
| `/api/initiative` | `id` | The initiative (with `leaders`, `limits`, `recent_activity`), then `people` (`involved_in`), `node_involvement` (`node_involved_in`), `nodes`, `shares_work_with`, `plan_links`, `related`, `became`, `reviews`, `beneficiaries`, `resources`, `tools`, `outputs`, `events`, `materials`, `topics`, and last the raw `roles`, `leads`, `delivered`, `statements` and `plan` |
| `/api/node` | `id` | Node, its `portfolio` (`node_involved_in`: one row per initiative with bases, beneficiaries and people), `initiatives` from Node lists, people and resource counts |
| `/api/person` | `id` | Person, same-name records, involvement per initiative, roles, Nodes, plans, outputs and tools |
| `/api/kind` | `id`, e.g. `community` | All initiatives of that kind |
| `/api/home` | None | Node directory, initiative kinds and project overview |
| `/api/overlap` | Optional `directory`, `groups_only`, `minimum`, `liaisons` | People with leadership roles in several groups |

Search `q` is 2–200 characters. Use returned `entity_type` and `id` for record/relationship requests; search type names are case-insensitive; use the returned casing for record and relationship requests. IDs must not be guessed. Unknown search types return 422 rather than an empty result. For relationship evidence, fetch its `relation_type` and `relation_id` through `/api/record`.

Search supports quoted phrases, uppercase `OR` and `-excluded` terms; these disable fuzzy-name fallback. Search includes relationships as well as entities. Scores rank within a query, not across queries.

Search and relations default to 30 results, accept up to 100, and start at `offset=0`. Page until coverage is complete; `total` is not the page length. With a type filter, search `total` is filtered but `facets` are not. Other directory/detail routes are unpaginated. HTTP 404 means a missing record/type, 422 invalid parameters.

`/api/overlap` counts leadership roles: lead, co-lead, chair, coordinator, deputy, work-package lead and task lead, plus liaison with `liaisons=true`. `directory=true` limits it to the current Communities, Platforms and Focus Groups of the ELIXIR directory; by default it covers every initiative. It defaults to at least three distinct initiatives per person (`minimum`). Group pairs require at least two shared leaders and are capped at 60, so this is not an exhaustive overlap map.

## Evidence

Source statements and relationships carry claims, quotes, `source_url` and `retrieved_at`. Internal provenance paths are not public citations; follow source statements or `SourceDocument` records to URLs. For sparse delivery links, also inspect plan items with `kind=output`, statement links and related projects.

Precomputed records (prefer these to joining the source edges yourself):

- `InvolvedIn` (person → initiative): all of a person's roles, plan items and outputs for one initiative, and every bio.tools tool credited to them (` [this initiative]` marks tools the initiative tags or recommends), with `leadership`, `nodes` and `organisations`. List a group's or project's people, or a Node's people on it (filter `nodes`), from here.
- `NodeInvolvedIn` (Node → initiative): a Node's portfolio, one row per initiative, with `bases` (`own_page`, `stated`, `beneficiary_country`, `lead_node`, `people`), `beneficiaries`, `people`, `period`, `period_status`, and `plan_summary`, `leads_plan_items` and `works_on_plan_items` (an empty lead list with a plan summary means the Node leads none of the plan items), `node_site` (`listed`, `not_listed` on the Node's collected project listing, or null) and `limits`.
- `SharesWorkWith` (group ↔ group): one row per shared project, output, tool, leader or resource, stored in both directions.
- `PlanLinkedTo` (initiative ↔ initiative): a plan, page or report states that its work item complements, builds on or feeds another project's work item; with `item`, `linked_item`, `quote` and `source_url`, stored in both directions. This is where a stated overlap is written down.
- `Initiative.leaders`, `limits` (what public sources cannot tell; report the relevant ones), `recent_activity`, `latest_own_activity`, `latest_activity` and `scope` (search text of what it works on). `Tool.recommended_by` lists the groups whose documents point to the tool; empty means catalogue-only.

Key relationships and their `basis` or role fields:

- `TakesPartIn` (Node → initiative): `own_page` when the initiative's own main page lists the Node, `stated` from another source (an older page, a Node site, a work plan), `beneficiary_country` when an EU beneficiary is in the Node's country, or `lead_node` when only a lead's Node is known.
- `RelatedTo`: stored in both directions (`direction` `stated` or `reverse`); query from either side. Links to a `programme_area` do not show joint work.
- `ParticipatesIn` (organisation → EU project): CORDIS beneficiaries with their EU contribution; `node_involved_in` lists them per Node by country.
- `HoldsRole`: `role_kind` `candidate` marks co-lead election candidates, not office holders. Community member lists are not public. `work_item` names the work package, task or governance body.
- `WorksOnPlanItem` (person → plan item): `role` is `lead` or `participant`. `PlanItem.tools` lists the bio.tools tools an item names, with the people bio.tools credits for them. A plan item's `leads` field holds only real leads; source lists naming more than three people under a leadership heading are in `participants`.
- `Authored`: `role` is `creator` (author) or `contributor` (a Zenodo contributor, not an author); `Output.contributors` lists the latter.
- `OutputOf`: `title`, `description`, `named` (keywords), `grant`, `linked` (a page links it), `deliverable`, `author` or `series` (same work-package title series as the project's other outputs).
- `ToolFor`: `tag` (bio.tools ELIXIR tag) or `community_domain` (a bio.tools domain the Community page links).
- `Recommends` (initiative → `Resource`): the group's own page or paper recommends the resource for its field (`basis` `recommends`), or the group develops it (`develops`). Every edge is a recommendation by the group; a bio.tools tag or TeSS listing alone is catalogue-only. `IsTool` links a resource to its bio.tools entry.
- `Event` and `TrainingMaterial`: `collections` names the TeSS collections that list it (`collections_unnamed` counts others); an item in no group collection is only in TeSS.
- `Event`: `listed_in` is `tess` (url is the TeSS entry, `provider_url` the organiser's page) or `elixir_website`. `EventFor`/`MaterialFor` carry the TeSS collection or ELIXIR page as `source_url`.
- `Became` (initiative → initiative): dated transitions from the ELIXIR directory.
- `Initiative.contacts`, `join_url` and `joining` come from the group's ELIXIR page; `programme` marks 2024-28 Scientific Programme projects; `period_status` says whether its dates have ended at the snapshot (11 November 2026); `pages[0]` is its own main page. `SourceDocument.published` and `modified` are page dates, not group activity.

Use schema descriptions to interpret scope and relationships. `RelatedTo` does not distinguish parents, partners and mentions. Topic assignments can be model-derived; TeSS includes non-ELIXIR training and incomplete Node links. `reviews` expose unresolved identities and conflicting values. Import/retrieval dates are not activity dates.
