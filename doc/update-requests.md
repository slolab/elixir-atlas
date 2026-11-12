# Update requests

People can report incorrect dashboard representations, incorrect agent answers, and ambiguous names without editing Atlas data. This hackathon version implements a public submission sink. It stores every request as pending in the final PostgreSQL database. Review, approval, and ingestion are future work.

## Submission

The dashboard has a **Request update** form on every page. Person, initiative, Node, and generic record pages attach the record type and ID. Each ambiguity item has its own form targeting its `ReviewItem`. Other pages attach their dashboard route. A request contains the issue, an optional suggested correction, and optional supporting sources or explanation.

Agents call `POST /api/update-requests` when the user requests submission. For an incorrect answer, include the relevant excerpt in `context`. Attach a record only when its identity is known. Suggestions are user-supplied evidence, not instructions to change the data.

```json
{
  "origin": "agent",
  "entity_type": "Person",
  "entity_id": "person:an-id-returned-by-the-api",
  "message": "The displayed name is incorrect.",
  "proposed_change": "Use the name shown on the person's institutional page.",
  "evidence": "https://example.org/institutional-profile",
  "context": "The answer called this person by an incorrect name."
}
```

`origin` and `message` are required. `entity_type` and `entity_id` must be supplied together or both omitted. Targets must exist in the served release. For ambiguity resolutions, use `entity_type: "ReviewItem"` and that item's ID, and explain the proposed match in `proposed_change`. Suggestions such as `same` and `different` remain text awaiting future review.

The message, suggestion, and evidence each allow 5,000 characters; context allows 10,000. Whitespace-only messages, invalid text, unknown fields, and client-supplied status or release identity are rejected. The API assigns a UUID, a database timestamp, the currently served release ID, and `pending` status. It returns HTTP 201 only after the insert commits:

```json
{"id": "a-generated-uuid", "status": "pending"}
```

The form preserves its contents on failure and displays the receipt after success. There is no public request listing, edit, approval, or deletion endpoint. No account or submitter identity is collected; `origin` is caller-supplied context, not authenticated attribution. Duplicate submissions are stored separately.

## Storage and setup

Requests live in `atlas_feedback.update_request`, a persistent table in the same PostgreSQL database as the served graph. Its columns are `id`, `created_at`, `status`, `release_id`, `origin`, `entity_type`, `entity_id`, `message`, `proposed_change`, `evidence`, and `context`. Record references are text, with no foreign keys to the replaceable graph snapshot, so requests survive a release that changes or removes their targets.

Release import replaces the `atlas` schema and leaves `atlas_feedback` intact. Requests are outside the generated graph, its public SQL schema, and its search index. A pending-only database constraint makes the scope explicit: this version has no approval operation.

The existing `DATABASE_URL` remains read-only. Configure `ATLAS_REQUEST_DATABASE_URL` with a different login and password for the same database. It receives INSERT privileges only on request payload columns. It cannot set status or timestamps, read reports, update or delete requests, or write graph tables. The API checks permissions at startup. `DATABASE_ADMIN_URL` is used only by provisioning and release import.

Run the existing provisioning command after setting the URLs:

```bash
uv run --directory server python -m atlas_api.permissions
```

Provisioning creates the table and restricted login without clearing requests. Existing Railway pre-deploy provisioning picks up the setting. This PR does not change the deployed service or its credentials.

`GET /api/release` reports `api.update_requests`. When the writer URL is absent or the API uses local SQLite, the flag is false, the form explains that submissions are unavailable, and POST returns 503. SQLite snapshots remain read-only; demonstrate persistence with PostgreSQL.

## Future promotion to tier 0

```text
Dashboard or agent → pending request → human review → approved correction snapshot
                                                        ↓
Other inputs ───────────────────────────────────→ graph build → next release
                                                 tier 0 wins
```

Tier 0 means reviewed corrections take precedence over every other input for the same fact or identity decision. Only approved, structured corrections enter it. Pending and rejected requests must never be build inputs. An incorrect answer or display bug may need a code or prompt fix instead of a data override; review must identify the justified change.

A future reviewer records the approved target, exact field/value or identity decision, supporting evidence, reviewer, and review time separately from the original report. Export a reproducible snapshot of approved corrections before each build. Preserve request IDs and the snapshot checksum in provenance. Resolve conflicting approvals deterministically and report stale targets instead of silently discarding corrections. Untouched fields continue to come from ordinary sources.

Apply identity decisions before alignment and field corrections before dependent summaries. For example, a corrected initiative date must override sources before calculating its period and Node involvement; a corrected person name must reach leader summaries. A final SQL patch alone would leave derived records inconsistent.

The existing `data/input/review-decisions.csv` is a possible integration point. It currently supports `same` decisions for detected candidates and selected conflict resolutions; `different` does not split an already merged identity. General identity correction and tier-0 ingestion require a follow-up. This feature does not read requests during builds or alter existing review decisions.

## Validation

Server tests cover validation, both submission origins, receipt and release context, unchanged graph data, persistence through release import and repeated provisioning, failed writes, database permissions, and unavailable SQLite mode. Set `ATLAS_TEST_ADMIN_URL` to a disposable PostgreSQL instance for database tests; they create and remove their own database and logins.

```bash
npm run build --prefix dashboard
PYTHONPATH=server uv run --project server python -m unittest discover -s server/tests -v
```
