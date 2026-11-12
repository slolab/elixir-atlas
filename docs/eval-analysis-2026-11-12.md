# Why build v2 scores 0.31 on atlas_261111

Run: `eval/results/atlas_261111-v2__skill-api__build-v2__gpt-6-luna` (gpt-6-luna, skill + local SQL API, release
`build-v2-candidate`, snapshot `20261111T204305Z`). Per-question evidence, with the SQL used to check each claim, is in
[eval-analysis-2026-11-12/](eval-analysis-2026-11-12/).

## Summary

The low score is mainly a data-representation problem. The report of 11 November said the opposite, and it was
wrong: the facts are mostly in the graph, but the agent cannot reach them, or the graph states them in a misleading
way.

The 21 questions have 101 scored components. The answers lost 45.5 of them:

| Cause | Lost | Meaning |
| --- | ---: | --- |
| Hard to reach | 18.5 | The fact is in the graph, but a view is too large, an edge points the "wrong" way, or a link between existing records is missing. |
| Wrong data | 5.5 | A field, kind, status or basis says something false or misleading, and the agent believed it. |
| Missing data | 5 | The fact is in the sources but not in the graph. |
| Seen, not used | 10.5 | The agent printed the fact and left it out. 7 of these are statements of absence, such as "the member list is not public". |
| Not queried | 3 | One obvious query would have found it. |
| Rubric | 3 | The reference asks for more than the question or the public data supports. |

So 29 lost components (64%) trace to the data layer and 13.5 (30%) to the agent. Most of the agent's own losses are
absence statements, which the graph keeps only as prose in schema descriptions.

Three full runs on this set scored 0.31: the baseline, the API and skill changes, and build v2. Each run is one
trial per question, and several verdicts have judge confidence below 0.65. Per-question gains and losses cancel, and
a single run cannot show a change of a few components.

## What stops the agent

### 1. Detail views are too large and start with the least useful part (about 9.5 components)

`/api/initiative` returns everything about a group in one response: median 96 KB, Systems Biology 159 KB, ELIXIR-STEERS
849 KB. Plan items are the largest part: 62% for STEERS and 75% for Systems Biology. The agent prints the first 7,000–18,000 characters, or the first item of each
list, so the roles, related projects and tools near the end never reach its context.

- 003: the RDM co-leads start at character 34,416, after 31 KB of plan items.
- 018: the co-leads, the shared co-lead Vitor Martins dos Santos and DBTLHub, which is second in `related`, were all in
  the response. The agent printed the first item of each list and answered with email addresses only.
- Also 004, 008, 010, 016, 020 and 021.

### 2. A relationship's direction depends on which page stated it (5 components)

`RelatedTo` points from the page that names the other initiative. Of 207 Community–project pairs, 150 exist only
project → Community. In 001 the agent queried Community → project and found 2 of RCI-M's 8 Communities and 2 of
DBTLHub's 6, which is exactly what it answered. That direction rule cost components 1–4 of 001 and part of 020.

### 3. Fields that mean something other than their name (5.5 components and several traps)

- `PlanItem.leads` holds the ELIXIR-STEERS website's "Leadership" list, which names up to 21 people per task. 18 of 29
  STEERS tasks have more than three "leads", Hedi Peterson among them. The real task leaders exist only as
  `HoldsRole` rows with free-text `work_item`. Result: 007 could not say that Tartu leads nothing.
- `role_kind`: the same "Leadership" block on two Community pages gives `lead` for Microbial Biotechnology and
  `co_lead` for Systems Biology. Anil Wipat also has a Node-site `member` row that sorts first.
- `Recommends.basis = lists` reads as "merely listed" (015). MetaNetX is kind `standard`, so it has no `IsTool` edge.
  SBML gets `recommends` from a to-do in a meeting report.
- `status`: HARVEST is `current` although it ended in June 2026, from a present-tense sentence (014).
- `kind`: DATAREX and three other projects on ELIXIR commissioned-service pages are `other_project`, because kind is a
  majority vote over Node pages (013). The "Cellular and molecular research" programme area is a
  `commissioned_service` related to 14 Communities, and the 020 answer used it as evidence of a joint project.
- "Own page": for several services the ELIXIR-UK page is listed first in `pages`, so its dates override the ELIXIR
  page. For example, fluxomics-workflows shows 2019-06 to 2021-05; the ELIXIR page says 2021-06 to 2021-11 (006).
- Old and new pages of a service are unioned as `stated` Node lists, so Compute and Training look UK- or
  German-listed when only the older page says so (013, 014).
- `OutputOf` with basis `grant` makes a 2026 FEGA white paper an output of CONVERGE and EXCELERATE, which ended in
  2023 and 2019 (013).

### 4. No link between records that exist (about 5 components)

- No `Organisation → ElixirNode` edge. TARTU ULIKOOL participates in STEERS, CONVERGE and EXCELERATE, but nothing
  connects it to ELIXIR Estonia, and Tartu is split over four Organisation rows (006).
- No plan item → tool edge. The "plant use case building on the Stress Knowledge Map" pilot is not linked to SKM or
  its developers (020, 021).
- No plan item → plan item edge across projects. The Training Platform plan's link to STEERS Tasks 4.1 and 4.3 is lost
  (010).
- STEERS governance (General Assembly, Heads of Nodes Committee) is mapped to Nodes and the ELIXIR-wide committee,
  not to the project (008).
- Zenodo outputs titled "BFSP CoS | WPn" are not linked to the project that owns WPn (013).
- Events and materials do not record their TeSS collection, so "in the Systems Biology collection" versus "only in
  TeSS" is unanswerable from a record (017).
- Split people: Mihail Anton (4 records), Marek Ostaszewski (2), Jorge Oliveira (2) and Ana Teresa Freitas (2).

### 5. Absences and limits are not data (10 components)

The scoring asks the agent to state limits in about 20 of 101 components. The graph keeps these limits only in prose,
inside long schema descriptions. Examples: the member list is not public, the STEERS grant agreement and effort per
task are internal, FAIRsharing and RDMkit were not crawled, and the bundle plan gives no owners, dates or funding. The
agent saw several of them and dropped them; others are not in the graph at all, such as the D1.6 handbook's statement
that the grant agreement lives on an internal drive.

### 6. Answers that need many joins (002, 006, 012, 013, 014, 019)

The agent must compute these from several tables, and it fails:

- the latest dated evidence for each group (002);
- whether a project has ended as of the snapshot (012, 014);
- a Node's portfolio: listed on which page, beneficiary, EU contribution, dates, conflicts (006, 013, 014);
- the people a public page names for a group (019).

009 is the contrast: the question named the organisation and the project, one `ParticipatesIn` query answered it, and
it is the only correct answer.

### 7. Extraction gaps

- Slack and the Communities Handbook's joining sections are not extracted (003, 004).
- `joining` is filled for 1 of 19 current Communities, and its hyperlinks are stripped. All 19 have `join_url`.
- The preprint "Making Models That Matter" is not an Output, and its ten recommendations are 10 of 42 ungrouped
  `practice` rows (016).
- F1000 posters, documents and slides have no abstract, and PDF document dates are null (002, 012).
- Cross-project links in plan text are not extracted (010).

### 8. A build v2 bug

The Systems Biology and Biodiversity Community pages contribute no `Recommends` edges: 18 extracted
recommendations are dropped. `superseded_snapshot` drops each page's `communities/` snapshot in favour of a newer
redirect file that the recommendations extraction never read (015).

## Agent behaviour

These cost time more than points.

- About three `/api/schema` calls per question. Snake-case table names such as `source_statement` fail.
- 013 took 70 steps, with 7 errors and one long query re-sent about ten times.
- No run queried `reviewitem`, which holds the date and Node conflicts.
- The model is a small one (gpt-6-luna, $0.86 for 21 questions), so the data must do more of the work.

## Per question

| Q | Verdict | Lost components (cause) | Most useful fix |
| --- | --- | --- | --- |
| 001 overlaps | failed | 1–4 hard to reach (edge direction) | Symmetric group–project links and a shared-work table |
| 002 inactivity | failed | 1 seen; 2 hard to reach; 3 rubric; 4 seen / hard to reach | Derived group activity dates |
| 003 RDM contact | partial | 2 hard to reach (view size); 5 missing (Slack) | Compact view with people and contacts |
| 004 onboarding | failed | 2 hard to reach (link stripped); 3 seen (absence); 4 missing (Handbook) | `joining` for every group, with links |
| 005 leaders | partial | 3 seen (agent excluded WP leads) | Current-directory scope and a leadership class |
| 006 Estonia portfolio | partial | 1 hard to reach (no Organisation → Node) | Node institutes and a Node portfolio |
| 007 STEERS commitments | failed | 1 wrong (`leads`); 4, 5 missing (not-public facts) | Split `leads`; gap records |
| 008 Estonia people | failed | 1, 4 hard to reach (governance, participants); 5 seen | Project governance roles; participant edges |
| 009 Tartu funding | correct | – | – |
| 010 Task 4.3 overlap | failed | 1 missing (cross-project link); 2 not queried; 3 hard to reach | Plan item → plan item links with quotes |
| 011 Compute webpage | partial | 4 seen (institution codes, not names) | Organisation and Node on each role |
| 012 FAIR-FEGA changes | partial | 1 seen (ended, no status update) | A derived period status |
| 013 de.NBI outputs | partial | 3 not queried (beneficiary); 4 wrong (DATAREX kind) | Kind from the main page; "CoS \| WPn" rule |
| 014 UK portfolio | partial | 1, 4, 5 half wrong (HARVEST status, Compute); 3 not queried | Main-page Node flag; Node portfolio |
| 015 GEM resources | partial | 4 wrong (`lists`, dropped pages); 5 seen / hard to reach | Fix the bug; "recommended vs catalogue-only" |
| 016 GEM reading | partial | 2 hard to reach (ten recommendations ungrouped) | Preprint as Output; list positions |
| 017 GEM training | partial | 3 hard to reach (no collection field) | `collections` on events and materials |
| 018 GEM contacts | failed | 2–4 hard to reach (view size, role kinds, shared leader) | People summary; shared leaders |
| 019 SB tool people | partial | 1 seen (not public); 2 rubric | Person-named-in-group edge; merge Anton |
| 020 SB partners | failed | 2 hard to reach; 4 rubric; 5 wrong (programme area) | Programme-area kind; shared-work table |
| 021 bundle feasibility | failed | 1 seen; 2 hard to reach (plan item → tool); 3 seen / hard to reach | Plan item → tool edges; person merges |

## Recommended changes

The list is ordered by the components each change targets for the effort it needs. The counts are targets, not a
promise of recovered points.

1. **Fix wrong data (about 6 components and several traps).**
   - Fix `superseded_snapshot` for recommendations.
   - Rename `PlanItem.leads` to the list it is, and link the real task leaders to their tasks.
   - Normalise `role_kind` from the same page layout.
   - Rank the ELIXIR page first as the own page.
   - Take kind from the main page and give programme areas their own kind.
   - Derive status from the end date.
   - Rename `Recommends` basis `lists` to `mentions`.
2. **An answer-shaped initiative view (about 9.5 components).** Return a short summary first: identity, period and
   status, contacts and joining, people (one row per person, with role kinds, organisation and Node), related groups
   and projects with shared people, counts, known gaps and open conflicts. Page plan items, outputs and statements
   separately.
3. **One-direction group links and a shared-work table (about 6 components).** Store group–project `RelatedTo` once in
   a fixed direction, or symmetrically. Derive Community pairs with what they share (project, output, tool, leader)
   and its source.
4. **Derived records for common questions (about 6 components).**
   - Per-group activity dates, with precision and whether the evidence is the group's own or indirect.
   - A period status as of the snapshot.
   - A Node portfolio from Organisation → Node edges.
   - Person-named-in-group edges.
5. **Gap records (about 10 components).** A small record type for stated limits, attached to the initiative or concept
   and returned in views: what is not public, which sources were not crawled, and what a plan leaves unstated.
6. **Extraction gaps (about 5 components).** Cross-project plan links, `joining` with links for every group, the
   Handbook and Slack sections, preprints as Outputs, F1000 abstracts and document dates.
7. **Eval method.** Run each question three times before comparing builds.
