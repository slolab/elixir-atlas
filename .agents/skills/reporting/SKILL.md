---
name: reporting
description: use before reporting the status or progress to the user to refine the reporting structure and tone.
---
The user follows many projects at once and reads messages between other work, so each message must make sense on its own, in one reading. The rules follow well-known frameworks from military command and clinical handoffs: BLUF, the Pyramid Principle, SBAR, SITREP and I-PASS. 

## Reporting
Follow the Pyramid Principle and BLUF: start with the answer, the state of the work or what you need, then give only the support the reader needs. Explain every ID in a few words, such as "R3, the Airtable milestone".

Write plain, compact English in the spirit of ASD-STE100 and the EASE guidelines: full sentences in the first person and the active voice, one idea per sentence, concrete statements, the words a colleague would use. Avoid what makes agent prose heavy: rhetorical emphasis, repeated conclusions, unnecessary qualification, parentheses, dramatic phrasing, cumbersome asides, overly assertive language, and long explanations of simple points.

Reports are short SITREPs, sent when a feature is ready or merged, when work is blocked, and when Vlad asks, in at most ten lines. The first sentence says whether the work is on track, at risk or blocked, and why. Then say what changed, which decisions you took alone, one line each, what comes next and what you need from Vlad.

> The feature that does XYZ has been implemented and reviewed. To complete, we need to create a database and decide on the filter.
>
> 1. Please create an Airtable base for testing. R3's live tests need their own base so that they never write to Anna's. Agents don't touch `.env`, so you need to add the base ID there as `AIRTABLE_TEST_BASE_ID` and give the token read and write access to the base.
> 2. Should R4's year filter apply only to papers? I recommend yes, because <reason>. If I don't hear from you by tomorrow, I'll go ahead with that.
>
> I also made these decisions myself:
> - A paper that shares its DOI with another paper now counts once in R2's export. I changed the spec wording to match.
> - The CHC total is 342, not 300, because the spec counts people under their main institute.
>
> After that is complete, we do <next steps>.

## Backbrief
When you start a milestone, or when the user changes direction, give a backbrief in at most eight lines: the goal as you understand it, your plan, your key assumptions, what you will decide alone and what will make you come back. Start when Vlad confirms. If his message gives no purpose or end state, ask for that part.
