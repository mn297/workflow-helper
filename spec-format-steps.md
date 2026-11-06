# Spec format, step chapters: one file an agent builds from, one step at a time

A spec is the one file a planning session hands to a fresh implementing session. The agent reads it with no other context. A human reviews it before and after.

This format cuts the work into **step chapters**. Each chapter holds everything one step needs: goal, files, requirements, contracts, tests and gate. A reviewer reads §1 to §3 and knows what changes, in what order, and how each step is checked. An agent that resumes at step N reads §1 to §5 and chapter N, and builds.

It replaces [`spec-format.md`](spec-format.md) for new specs. That format sorts the work by kind (requirements by part, files by path, tests by ID, steps last), so one step's work sits in four places, joined only by IDs. Agents miss items in that join, most of all after a context compaction or a fresh-session resume. A chapter is also a ready prompt for one subagent.

Sources: EARS requirement patterns (Mavin), RFC 2119 keywords, Gherkin Given/When/Then, ADR columns (Nygard, MADR), Google design-doc non-goals, GitHub spec-kit's clarification marker and exact paths, OpenAI ExecPlans (self-contained, milestones that each verify on their own), Claude Code best practices ("define done").

## Outline

Headings in this order. Each line says what goes in and why.

| # | Section | What goes in | Why |
|---|---|---|---|
| 0 | Header table | status and date, branch and base, state file path, test commands, notation line | reader sees where to work and how to check before anything else |
| 1 | Result | one paragraph, then **Done when**: 3 to 6 observable checks, each said in words, then its test IDs | answer first; an agent stops when work looks done unless it has a check |
| 2 | Change at a glance | a Today diagram; an After diagram with each node marked new or changed; a table Today, After, Step that names every module created, split, moved or deleted; a short "Stays the same" list | the reviewer sees the diff before the detail; the agent sees what to delete |
| 3 | Step map | table: step, what works after it, main files, gate in words | the index of the chapters and the build order, on one screen |
| 4 | Context | problem (the owner's words, one story of what fails today), terms, scope (out of scope, anti-goals as MUST NOT rules), facts tagged **measured**, **read** or **assumed**, open questions | the why, read once |
| 5 | Seams | the interfaces between parts and the flows across them: shared contracts, on-disk formats, sequence and state diagrams, import boundaries; "Why" folded in `<details>` | every step builds against them; one source of truth, so chapters point here instead of copying |
| | Step 1 … Step N | one chapter per step, in build order, in the form below | a chapter plus §5 is enough to build that step |
| | Decisions | one table: ID, decision, rejected options, why, cost if wrong, who decided | one place for every ruling |
| | Risks | table: risk, cost if it bites, mitigation | keep short |
| | Verification and report | the whole-build check: commands with expected output, measurements to fill, what to report, the owner's hands-on checks | evidence before claims |
| | How to run this | read order, branch, state file, environment rules, job rules | instructions last, after the material they act on |
| A | Appendix | long reference tables, measurement commands, rejected alternatives | keeps chapters short |

Number §1 to §5. Name chapters `Step N: <title>`. Refer to them as "step 4", and to their parts as "step 4, Design".

## Step chapter

Every chapter has these parts, in this order, with these bold labels:

```markdown
## Step N: <title>

**Goal.** One sentence: what works after this step that did not work before.

**Start state.** What earlier steps left that this step uses. Which tests already fail, and which step fixes them.

**Changes.** Touch only these files.

| Path | Action | What changes | R |
|---|---|---|---|
(Action is one of: create, edit, move, delete.)

**Requirements.** `R<n>` in EARS form, each ending `Tests: <IDs>`.

**Design.** Contracts, rule tables and diagrams that only this step uses. For shared ones, a pointer to §5.

**Tests.**

| ID | Given | When | Then | R |
|---|---|---|---|---|

**Gate.** Commands with expected output; the step is done when they pass. Then the tests allowed to fail after this step, each with the step that fixes it, or "none". Then what to write in the state file.
```

Rules for chapters:

- §5 holds the seams. A chapter holds its step's insides: rule tables, algorithms, command output, its own routes and settings. A chapter plus §5, plus the code earlier steps wrote, is enough to build its step.
- Record goldens of the old code in the first step that changes it, before anything is deleted.
- A file that two steps touch appears in both Changes tables. Each row says that step's change only.
- Each requirement lives in one chapter: the step that builds it.
- Each test lives in the chapter of the first step where it can pass. A test that needs a later step's code goes in that later chapter.
- The gate names allowed failures by test file or test ID. Any other failure is a bug in this step.
- A chapter longer than about 150 lines is two steps.
- Work that only the owner can do (keys, hardware, accounts, live services) is the last chapter.

## Writing rules

- Short sentences, active voice, simple tenses. Answer first. Define a term at first use.
- Keep hedges that carry meaning ("may", "likely", "untested"). Never turn a guess into a flat claim.
- Uppercase MUST, SHALL, MUST NOT, MAY carry RFC 2119 force. Lowercase "must" is prose.
- Numbers with units. Say how each number was found.
- Name files by path. Name functions and flags only where the reader has to go there.
- Say each check in words first, then give its IDs. IDs point to text; they never replace it.
- Write the file in reading order. A "read §7, then §6" line means the order is wrong.
- Mark who owns a choice: owner, planner, or builder call. A builder call names its cost if wrong.

## Requirement form (EARS)

One trigger, one actor, one response. Pick the pattern that fits:

| Pattern | Shape |
|---|---|
| Ubiquitous | The `<part>` SHALL `<response>`. |
| Event | When `<trigger>`, the `<part>` SHALL `<response>`. |
| State | While `<state>`, the `<part>` SHALL `<response>`. |
| Unwanted | If `<condition>`, then the `<part>` SHALL `<response>`. |
| Optional | Where `<feature is present>`, the `<part>` SHALL `<response>`. |

Each requirement ends with `Tests: <IDs>`. A requirement with no test is a smell: either add the test or move the text to Design as a contract.

Example:

> **R4 Wheel.** When the wheel turns one notch over the axis, the view SHALL zoom about the cursor by 1.2 per notch, clamped to 30 s to 48 h. Tests: B2.

## Test row form

| ID | Given | When | Then | R |
|---|---|---|---|---|
| B2 | a 1 h view | one wheel notch at x = 30 % | view shrinks by 1.15 to 1.25; cursor time moves under 1 % of the view | R4 |

The ID prefix gives the level, for example `F` fast unit, `S` slow integration, `B` browser, `C` cost or performance, `H` hands-on by the owner. Name the prefixes in the header's notation line. Measurements that produce a number rather than pass/fail still get a row; the Then column says what to record. A measurement row may name the decision it checks in place of a requirement.

## Decision row form

| # | Decision | Rejected | Why | Cost if wrong | Who |
|---|---|---|---|---|---|
| D5 | Store keyed by folder hash | masking at read time | hides old data with no logic | one folder level in the store | planner, after review |

Decisions taken after a builder check or a review go in the same table with "after review" in Who. No separate "rulings" section. Chapters cite decisions by ID; the reason lives only in this table.

## Diagrams (Mermaid)

- Use `flowchart` for structure and data flow, `sequenceDiagram` for one flow in time, `stateDiagram-v2` for a mode machine, `erDiagram` for stored data. Avoid Mermaid's C4 syntax; it is experimental and lays out by source order.
- Under about 15 nodes per diagram. A label on every arrow, more than one word. A title or one sentence above the block.
- The same facts in text. The requirements, not the picture, are the contract.
- §2 diagrams: mark each node of the After diagram in its label text, `(new)` or `(changed)`. A `classDef` colour may repeat the mark, never replace it. Deleted parts appear only in the Today diagram and in the change table.
- Gotchas: a lowercase `end` as node text breaks flowcharts and sequence diagrams; a node starting with `o` or `x` right after an arrow misparses; quote labels with punctuation; HTML entities such as `&lt;` vanish, so write `DAY` not `<day>`; a semicolon inside a `stateDiagram` note splits it; misspelled settings fail silently.
- Validate before committing. Headless Chromium with Playwright and `mermaid.parse` from a CDN build checks every block in a few seconds. GitHub and Obsidian both render `mermaid` fences.

## Length

§1 to §3 read in about 5 minutes (about 100 lines); that is the reviewer's path. A chapter reads in about 5 minutes (under about 150 lines). The whole file matters less: the agent reads §1 to §5 and one chapter at a time. Past about 10 steps, split the work into two specs.

## Process around the file

1. Plan: write the spec. Measure what can be measured in minutes; tag the rest assumed.
2. Builder check: a fresh subagent reads only the spec. It lists what it would still have to guess. It also picks two chapters and says what it could not build from that chapter plus §5 alone. Sort its questions: answered (put the answer in), minor (settle it, log in Decisions), owner's (ask in one message). Fix every statement it found contradicting the code.
3. Commit the spec. Stop. Implementation starts in a fresh session from the file alone.
4. The implementing session keeps a state file beside the spec: steps done, measurements, rulings with cost if wrong, next step. A fresh session resumes from its last "Next step" line.

## Checklist before commit

- Done-when list has 3 to 6 checks, each said in words and naming tests.
- The §2 change table names every module created, split, moved or deleted, with its step.
- Step map rows match the chapter headings, one to one.
- Every chapter has the seven parts in order.
- Every requirement sits in exactly one chapter and has a test ID. Every test row names a requirement, or for a measurement, a decision.
- Every gate ends with a "State file:" line.
- No test sits in a chapter before the step whose code it needs.
- Every gate lists its allowed failures, or says "none".
- Every open question names the step that answers it and a fallback.
- Every decision has a cost if wrong and an owner.
- Every file path is exact.
- Facts tagged measured, read, or assumed.
- Mermaid blocks parse.
- §1 to §3 fit in about 100 lines; every chapter in about 150.
