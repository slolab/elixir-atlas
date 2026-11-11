# Atlas API

Base URL: `https://atlas-production-d392fb6d.up.railway.app`

Requests return JSON without authentication. URL-encode GET parameters and send SQL as a JSON POST body. Full endpoint details: [API docs](https://atlas-production-d392fb6d.up.railway.app/docs).

## SQL

Check `/api/release`. When `api.sql` is true, read `/api/schema?format=sql` for the served release's PostgreSQL tables, types, descriptions, foreign keys, supported functions and limits. Reuse it during the investigation. Otherwise use the GET routes below.

`POST /api/query` accepts `{"sql":"SELECT ...","limit":1000}`. It supports one read query with joins, CTEs, subqueries, unions, aggregates and window functions. FROM functions require `WITH ORDINALITY`, for example `unnest(i.pages) WITH ORDINALITY AS u(url, position)`. Dates may be text with varying precision; read their descriptions before casting. Count distinct entity IDs when several source-specific edges describe the same relationship.

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
| `/api/initiative` | `id` | Initiative, plans, roles, outputs, statements and resources |
| `/api/node` | `id` | Node, initiatives, people and resource counts |
| `/api/person` | `id` | Person, roles, Nodes, plans and outputs |
| `/api/kind` | `id`, e.g. `community` | All initiatives of that kind |
| `/api/home` | None | Node directory, initiative kinds and project overview |
| `/api/overlap` | Optional `groups_only`, `minimum`, `liaisons` | Shared leadership roles |

Search `q` is 2–200 characters. Use returned `entity_type` and `id` for record/relationship requests; types are case-sensitive and IDs must not be guessed. For relationship evidence, fetch its `relation_type` and `relation_id` through `/api/record`.

Search supports quoted phrases, uppercase `OR` and `-excluded` terms; these disable fuzzy-name fallback. Search includes relationships as well as entities. Scores rank within a query, not across queries.

Search and relations default to 30 results, accept up to 100, and start at `offset=0`. Page until coverage is complete; `total` is not the page length. With a type filter, search `total` is filtered but `facets` are not. Other directory/detail routes are unpaginated. HTTP 404 means a missing record/type, 422 invalid parameters.

`/api/overlap` defaults to three distinct initiatives per role holder; `liaisons=true` includes liaison roles. `groups_only=true` excludes projects. Group pairs require at least two shared leaders and are capped at 60, so this is not an exhaustive overlap map.

## Evidence

Source statements and relationships carry claims, quotes, `source_url` and `retrieved_at`. Internal provenance paths are not public citations; follow source statements or `SourceDocument` records to URLs. For sparse delivery links, also inspect plan items with `kind=output`, statement links and related projects.

Use schema descriptions to interpret scope and relationships. `RelatedTo` does not distinguish parents, partners and mentions. Topic assignments can be model-derived; TeSS includes non-ELIXIR training and incomplete Node links. `reviews` expose unresolved identities and conflicting values. Import/retrieval dates are not activity dates.
