# CQ authoring and review

This set covers the 21 existing use cases using public-source snapshot
`20261111T134918Z`, with 11 November 2026 as the answering date. Version 2
incorporates Vlad's feedback on six version 1 records in Argilla.

## Realistic questions

Judge each question as something a person might type before doing the research.

1. Use only context the speaker could plausibly know before asking. Source
   locations, document identifiers and known discrepancies often come from our
   research and should stay in the grading notes.
2. Let intent remain implicit. A question does not need an invented persona,
   background story or explanation of why the answer matters.
3. Allow ordinary shorthand, omissions and uneven detail. Keep enough of a
   name, topic or time reference to make a standalone question intelligible.
4. Leave evidence discovery and answer structure to the answering agent.
   Remove instructions that prescribe sources, fields, checks or methods.
5. Keep variation natural. Short questions can be imperfect; artificial typos,
   forced slang and a uniform conversational template do not make them real.
6. Grade the words that were actually asked. Accept reasonable interpretations
   and assumptions instead of enforcing an unstated scope or exhaustive list.

The prompts are authored examples informed by the user stories and annotation
feedback. They are not transcripts of observed user queries.

## Reference answers and scoring

Lead with the answer or action that fits a reasonable interpretation. Give
enough detail to be useful, with links beside the relevant facts and resources.
Keep evidence limits where they change the answer. Put research distinctions,
alternative examples and pitfalls in `eval_notes`.

The reference answer is one supported response. Its ordering, wording and
choice of examples are not mandatory. Broad questions can receive a useful
selection; any claim to completeness needs evidence for that coverage.

Correctness and usefulness are separate scores. Useful prose cannot repair a
false conclusion. Factual coverage alone does not make an answer readable or
helpful. Version 2 requires a new evaluation baseline because both the prompts
and grading criteria changed.

## Factual review

Review against the frozen source files listed in each question. Keep source
statements separate from interpretations: a catalogue tag does not establish
endorsement, an author list does not establish staffing capacity, and missing
public evidence does not establish inactivity or lack of funding.

Two reviewers checked and revised the questions in separate groups, and a
third reviewed realism, tone and the fit between each question and its scoring.

## Raw-data fairness review, 12 November 2026

The objective is an answerable question and a fair judgment, not an agent
that always succeeds. Classify failures before changing the set:

- **Agent error:** relevant evidence exists in the supplied snapshot, but
  the agent misses it, misreads it or makes an unsupported claim. Keep the
  factual requirement; do not insert source names or answer hints.
- **Question ambiguity:** a reasonable reading differs from the scope the
  evaluator expects. Accept that reading or add the smallest natural anchor.
- **Evaluation mismatch:** a supported answer loses credit for an unstated
  requirement, optional detail or misread evidence. Correct the grading
  criteria or evidence notes, preserving factual standards.
- **Evidence limit:** the public record cannot establish a private fact,
  complete inventory or future commitment. A supported, appropriately
  bounded answer must be eligible for full credit. Partial answerability
  does not require the agent to invent the missing information.

The frozen version 2 baseline ran all 21 questions against raw snapshot
`20261111T134918Z`, using `openrouter/openai/gpt-6-luna` with high reasoning.
Its mean automatic scores were 0.81 correctness and 0.88 usefulness. Three
reviewers checked answers, traces and source evidence independently.

| Question or criterion | Diagnosis | Change |
| --- | --- | --- |
| 002, quiet Communities | “Lately” permits different periods | Say “over the past year”; record recent Metabolomics evidence in grading notes |
| 008, Estonia's people | Node roles and project activities are both plausible readings | Add “on Estonia's ELIXIR projects” |
| 013, Germany's outputs | General Node activity differs from project outputs | Add “across its projects” |
| 021, bundle feasibility | September has more than one relevant output | Specify “at its September meeting”; keep pilots and sources out of the question |
| 003, joining a Community | Accurate joining route penalized for omitted sign-in wording | Keep approval required; make the incidental sign-in detail optional |
| 005, shared participants | A supported selection treated as a mandatory census | Accept non-exhaustive examples across groups |
| 012, updating FAIR-FEGA | Valid status-update advice penalized for missing one reference discrepancy | Accept other evidenced update needs |
| 013, German attribution | Judge rejected a contribution explicitly credited to ELIXIR-DE | Record the Training D4.4 attribution in the evidence notes |
| 021, feasibility advice | A proposed next step was required as a factual component | Make it optional for a complete feasibility assessment |
| Shared grading | Brief orientation penalized; qualified search limits broadened into absence claims | Accept relevant opening context and judge qualified claims as written |

Regrading eight unchanged baseline answers removed five identified unfair
penalties: joining instructions, participant coverage, the brief Estonia
introduction, page-update advice and the qualified training-resource search.
Three controls retained their grades: a dense project list still lost
usefulness credit, a funding answer stayed correct, and the answer about
the wrong bundle still failed correctness. This checks grading behavior;
it does not establish better agent retrieval.

The four clarified questions each ran twice more. All eight trials completed.
Estonia answers still missed available project-plan evidence. Both bundle
answers still missed the meeting report and assessed a different proposal.
The Community and Germany answers had mixed coverage. These are agent
failures, not reasons to supply more hints or relax factual requirements.
Review also identified two Germany grading errors: the explicit D4.4
attribution and a Node-labelled publication archive being overlooked.
The latter answer still lacked project-output links; correcting attribution
does not make its coverage complete.

All 29 raw trials retain answers, grades and trajectories. The final D4.4
evidence note and optional-next-step change were reviewed after the runs
and were not regraded. There is no full post-calibration score or claim of
improved agent performance. Original grades remain available alongside
the evidence-based review. Local, ignored artifacts are in
`eval/results/cq-v2-raw-review-20261112/`: `comparison.json`, frozen CQ sets,
`paired-grading.json` and the three reviewer reports. A repeated-trial
console-report sorting error was fixed and checked against the saved grades.
