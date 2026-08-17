---
name: writing-docstring-summaries
description: >
  Use when writing or rewriting a module, class, or public-function docstring,
  or a comment on code you add or change. Covers summary lines that read as a
  noun pile, a label, team jargon ("adapter", "stand-in"), or a spec citation;
  comments that are bare labels or lack a unit, source, or measured cause; and
  field notes (dates, spec sections, "per decision X", change history) in
  either. Also for "docstring style", "comment style", "verb analog cadence".
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docstrings, Prose, Comments, Readability"
  category: "writing"
---

# writing-docstring-summaries

The summary line is one sentence that gives a reader a picture. Not a label.
PEP 257 and the project style fix the mechanics. This skill picks the sentence.

> [verb] a [real analog] feeding the [named payload], [cadence].
>
> `Emulate a live weather station feeding the reading-stream contract, one sample at a time.`

Answers: what is this pretending to be, what does it emit, how often.

## Pick the shape first

Match the shape to what the code is. Fill only the slots that exist in reality.
An invented analog or cadence is worse than a noun pile.

| The thing is... | Summary-line shape |
|---|---|
| Stands in for a real system **and** emits on a clock/step (replay, emulator, fake device, pump) | verb + analog + payload + cadence |
| Time-shaped, no real-world analog (renderer loop, iterator, scheduler) | verb + payload + cadence |
| One-shot transform (ingest, parser, materializer, exporter) | verb + input → named output contract |
| Pure functions or values (math, texture, constants) | verb the effect, or a noun phrase naming the thing + what needs it |
| Registry, seam, index, protocol module | noun phrase naming the seam + what it decides |
| Data class or state object (dataclass, NamedTuple, TypedDict) | noun phrase naming the state it carries + its owner or lifetime, unless obvious |

An analog is something a reader outside this repo already knows. If none
exists, drop the slot.

## The slots

1. **Verb**: what the code does (`Emulate`, `Replay`, `Ray-cast`, `Yield`).
   Functions and methods use the imperative (`Emulate`, not `Emulates`). A
   module may lead with a noun phrase; stay consistent inside one file.
2. **Analog**: the real thing (`a live weather station`), not the internal role
   (`stand-in`, `adapter`, `source`).
3. **Payload**: the message or type names (`Reading`, `Snapshot`, `Correction`),
   not a category word (`reading-stream source`).
4. **Cadence**: the time or step shape (`one Reading per sample`, `every
   stride`). For streams and replays, cadence is the point.

## Hard rules for line 1

- True first. State no role, payload, cadence, ordering, unit, or guarantee that
  the code does not support. When unsure, drop the slot. A missing fact costs
  the reader a look at the code. A false one survives review.
- One sentence on one physical line, inside the project's line length
  (`pyproject.toml` / `ruff.toml`; count the opening `"""`), ending in a period.
- Add words the signature does not already say: no signature, no parameter
  names, no repeat of the identifier. `def replay_log(): """Replay a log."""`
  adds nothing.
- No title-case label, no line that ends in a colon.
- No citation. A stable external source may close the body.

## The rest of the docstring

Then 2–4 sentences: where the data comes from, what this is not, who consumes
it, the constraint that will bite. Rationale comes last, then a stable external
source (paper, standard, upstream file) if one exists.

```python
"""Emulate a live weather station feeding the reading-stream contract, one sample at a time.

``replay_log`` walks a recorded log dir (a synthetic log, a field export,
or a finished live session) and yields the same messages a live station
would: one Reading per sample, plus a Snapshot every ``stride`` samples.
There is no sensor on this path. Values come from readings_ref.csv, not
from hardware.

``script_corrections`` wraps any source to mimic a smoother's
arrival-then-revise shape for consumer tests: it perturbs snapshot values
at arrival and later corrects them with Correction batches.
"""
```

## Reject these leads

| Bad | Why |
|---|---|
| `File-replay reading-stream source + scripted synthetic corrections.` | Noun pile, no verb. Reader must decode the architecture before the sentence means anything. |
| `Stand-in for a live station (spec section 4).` | No verb, no payload, no cadence, and a spec cite. |
| `The recorded adapter of the reading-stream contract:` | "Adapter" is a team word, not a picture. Ends in a colon. |
| `Replay the log by replaying the log dir.` | Same words as the identifier. Zero added information. |

## Already good: leave as is

These leads pass with slots missing, because those slots do not apply.

| Lead | Why it passes |
|---|---|
| `Ray-cast depth images from an arbitrary triangle mesh, no simulator needed.` | Verb + payload. A renderer emulates nothing and has no cadence. |
| `Archive ingest: one station dir -> the source/ contract.` | One-shot transform: input → named output contract. |
| `Source layer seam: what supplies a run's sample stream.` | Seam module. Noun phrase naming the seam is the honest shape. |

Edit an existing summary only for one of these reasons:

- It is wrong or stale.
- It fails a hard rule above.
- You edit that docstring for another reason.

Resemblance to a template is not a reason.

## Comments on lines you write

A comment carries a fact the reader cannot get from the code. Four kinds earn
their place:

| Comment on | It carries | Example |
|---|---|---|
| A constant or configuration value | unit first, then where the value comes from | `MAST_HEIGHT = 10.0  # m, anemometer over the ground (WMO standard exposure)` |
| A choice that looks arbitrary | the cause you measured, with the numbers | `# The library default of 60 s between polls misses gusts, and the daily peak then reads 4 m/s low.` |
| A frame, sign, shape, or index order | the convention the next line depends on | `# Wind direction names where the wind comes from, so the plotted vector takes the opposite sign.` |
| An ordering constraint | what must come first, and why | `# A thread pool makes each small matrix solve 30 times slower. This must happen before numpy loads.` |

- Write a block comment as full sentences: a capital letter, a verb, a period.
  A label (`# armature`, `# per-kind worst`) is not a comment. Write the
  sentence it stands for, or delete it.
- A trailing comment on a value can be a unit and a phrase (`# m, bump top`,
  `# (N, 4) xyzw`).
- Name units, frames, and sources exactly: `rad`, `T_W_imu`,
  `WMO-No. 8 (wind chapter)`.
- A number beats an adjective: "reads 4 m/s low", not "reads low".
- State only units, frames, causes, and measurements that you read in the code
  or got from a run. When unsure, or when the code already says it, write no
  comment.

## Describe the code, not its history

Docstrings and comments describe the code as it is now. A reader next year has
the code, not your spec, your plan, or this session. Field notes go in the
commit message or the PR:

- dates and phase or task names (`2024-03-07`, `Phase 2`, `Task 3`)
- pointers to a spec, plan, or review (`spec section 4`, `see plan.md`, `per review`)
- decision and ticket ids (`per decision D3`, `JIRA-412`, `as agreed`)
- change history (`now uses`, `was 60`, `changed to`, `no longer`, `fixed:`)

Write the reason itself, not where it was decided:

| Field note | Present fact |
|---|---|
| `# Per decision D3 (2024-03-06), use float64.` | `# float64: in float32, a timestamp after one hour rounds to 0.24 ms steps.` |
| `"""Replay a log dir (spec section 4, Phase 2)."""` | `"""Replay a recorded log dir as live Reading messages, one per sample."""` |

Name a source only when the reader can open it and it will not move: a paper, a
standard, a datasheet, an upstream file. A measured number stays. The date of
the measurement goes.

This section covers every docstring and comment you write, test bodies and
private helpers too.

## Scope

- Applies to: module, class, and public-function docstrings, a leading comment
  that says what a file *does*, and comments on lines you add or change.
- Not: commit messages, chat, test bodies, docstrings of private helpers.
- Touch only what is in scope. Leave other docstrings and comments in the same
  file as they are, also the ones that fail the tables above.

## Self-check

Before you leave a docstring or comment:

1. Every slot you filled exists in the code: no invented analog, no cadence on
   a thing without a clock, payload types named.
2. A reader who does not know this repo can picture the subject from line 1.
3. Line 1 passes every hard rule.
4. Each comment carries a unit, a source, a measured cause, a convention, or an
   order constraint.
5. Nothing you wrote holds a date, a spec or plan pointer, a decision or ticket
   id, or change history.
6. You changed nothing out of scope, and no summary outside the edit reasons.
