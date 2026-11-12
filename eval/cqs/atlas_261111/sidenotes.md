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
