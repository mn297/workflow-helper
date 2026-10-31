# Spec format: one file for a coding agent and a human reviewer

A spec is the one file a planning session hands to a fresh implementing session. The agent reads it with no other context. A human reviews it before and after. This format serves both: result and done-checks first, numbered requirements that tests point at, one decisions table, diagrams as text, run instructions last.

Sources behind the choices: EARS requirement patterns (Mavin), RFC 2119 keywords, Gherkin Given/When/Then, ADR columns (Nygard, MADR), Google design-doc non-goals, GitHub spec-kit's clarification marker and exact paths, Diátaxis for the appendix, OpenAI ExecPlans and Claude Code best practices for "self-contained" and "define done".

## Outline

Headings in this order. Each line says what goes in and why.

| # | Section | What goes in | Why |
|---|---|---|---|
| 0 | Header table | status and date, branch and base, state file path, test commands, notation line | reader sees where to work and how to check before reading anything |
| 1 | Result | one paragraph, then **Done when**: 3 to 6 observable checks, each naming test IDs | answer first; an agent stops when work looks done unless it has a check |
| 2 | Problem and terms | the owner's words quoted, one concrete story of what fails today, a terms table | one specific story beats a list of needs; every term of art defined |
| 3 | Scope | in scope, out of scope, anti-goals as MUST NOT rules | non-goals bound the work; anti-goals become testable |
| 4 | Facts | one table, each row tagged **measured**, **read**, or **assumed**, with how it was found | reader sees which numbers are firm |
| 5 | Open questions | table: ID, question, expected answer, which step answers it, fallback | mark gaps instead of letting the agent guess |
| 6 | Requirements | numbered `R1`, `R2`, ... in EARS form, grouped by component, each naming its test IDs | one sentence per behavior; easy to review and check off |
| 7 | Design | overview diagram, a sequence diagram per key flow, a state diagram per mode machine, then one subsection per component with contracts as tables or code blocks; "Why" folded in `<details>` | humans scan pictures; agents read contracts; rationale stays but folds away |
| 8 | Decisions | one table: ID, decision, rejected options, why, cost if wrong, who decided | one place for every ruling; conflicting instructions hurt more than gaps |
| 9 | Files | table: path, new or changed, what changes, requirement IDs | exact repository paths, not descriptions |
| 10 | Tests | table: ID, level, Given, When, Then, requirement IDs; each written red first | tests beside requirements improve generated code; one observable outcome per row |
| 11 | Risks | table: risk, cost if it bites, mitigation | keep short |
| 12 | Verification and report | commands with expected output, measurements to fill, what to report, the human's hands-on check | evidence before claims |
| 13 | How to run this | read order, branch, state file, environment rules, job rules, step table (step, work, requirement IDs, gate) | instructions last, after the material they act on |
| A | Appendix | long reference tables, measurement commands, rejected alternatives | keeps the body short |

Length: the body through section 12 reads in about 15 minutes. Beyond that, split the work into two specs.

## Writing rules

- Short sentences, active voice, simple tenses. Answer first. Define a term at first use.
- Keep hedges that carry meaning ("may", "likely", "untested"). Never turn a guess into a flat claim.
- Uppercase MUST, SHALL, MUST NOT, MAY carry RFC 2119 force. Lowercase "must" is prose.
- Numbers with units. Say how each number was found.
- Name files by path. Name functions and flags only where the reader has to go there.
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

| ID | Level | Given | When | Then | R |
|---|---|---|---|---|---|
| B2 | browser | a 1 h view | one wheel notch at x = 30 % | view shrinks by 1.15 to 1.25; cursor time moves under 1 % of the view | R4 |

ID prefixes by level, for example `F` fast unit, `S` slow integration, `B` browser, `C` cost or performance. Measurements that produce a number rather than pass/fail still get a row; the Then column says what to record.

## Decision row form

| # | Decision | Rejected | Why | Cost if wrong | Who |
|---|---|---|---|---|---|
| D5 | Store keyed by folder hash | masking at read time | hides old data with no logic | one folder level in the store | planner, after review |

Decisions taken after a builder check or a review go in the same table with "after review" in Who. No separate "rulings" section.

## Diagrams (Mermaid)

- Use `flowchart` for structure and data flow, `sequenceDiagram` for one flow in time, `stateDiagram-v2` for a mode machine, `erDiagram` for stored data. Avoid Mermaid's C4 syntax; it is experimental and lays out by source order.
- Under about 15 nodes per diagram. A label on every arrow, more than one word. A title or one sentence above the block.
- The same facts in text. The requirements, not the picture, are the contract.
- Gotchas: a lowercase `end` as node text breaks flowcharts and sequence diagrams; a node starting with `o` or `x` right after an arrow misparses; quote labels with punctuation; HTML entities such as `&lt;` vanish, so write `DAY` not `<day>`; a semicolon inside a `stateDiagram` note splits it; misspelled settings fail silently.
- Validate before committing. Headless Chromium with Playwright and `mermaid.parse` from a CDN build checks every block in a few seconds. GitHub and Obsidian both render `mermaid` fences.

## Process around the file

1. Plan: write the spec. Measure what can be measured in minutes; tag the rest assumed.
2. Builder check: a fresh subagent reads only the spec and lists what it would still have to guess. Sort its questions: answered (put the answer in), minor (settle it, log in Decisions), owner's (ask in one message). Fix every statement it found contradicting the code.
3. Commit the spec. Stop. Implementation starts in a fresh session from the file alone.
4. The implementing session keeps a state file beside the spec: steps done, measurements, rulings with cost if wrong, next step. A fresh session resumes from its last "Next step" line.

## Checklist before commit

- Done-when list has 3 to 6 checks, each naming tests.
- Every requirement has a test ID. Every test row names a requirement.
- Every open question names the step that answers it and a fallback.
- Every decision has a cost if wrong and an owner.
- Every file path is exact.
- Facts tagged measured, read, or assumed.
- Mermaid blocks parse.
- Body reads in about 15 minutes.
