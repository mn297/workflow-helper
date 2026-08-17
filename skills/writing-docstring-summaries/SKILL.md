---
name: writing-docstring-summaries
description: >
  Use when writing or rewriting a module, class, or public-function docstring
  and the summary line reads as a noun pile, a title-case label, a team-jargon
  role ("adapter", "source", "stand-in"), or a spec citation. Also use when the
  user says "docstring style", "verb analog cadence", "clearer docstring",
  "emulate a live ...", or asks that a new reader be able to picture what a
  producer / stream / replay / ingest module does.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docstrings, Prose, Comments, Readability"
  category: "writing"
---

# writing-docstring-summaries

The summary line is one sentence that gives a reader a picture. Not a label.

This sits **on top of** PEP 257 / the project's docstring style, which fix the
mechanics (one line, period, blank line, no signature restating) but say nothing
about *which* sentence to write. This does.

> [verb] a [real analog] feeding the [named payload], [cadence].
>
> `Emulate a live tracker feeding the posed-stream contract, one time step at a time.`

Answers: what is this pretending to be, what does it emit, how often.

## Pick the shape first

Not every module has an analog; not everything has a cadence. Match the shape to
what the code is. A slot that does not exist produces an invented metaphor —
worse than a noun pile.

| The thing is... | Summary-line shape |
|---|---|
| Stands in for a real system **and** emits on a clock/step (replay, emulator, fake device, pump) | verb + analog + payload + cadence |
| Time-shaped, no real-world analog (renderer loop, iterator, scheduler) | verb + payload + cadence |
| One-shot transform (ingest, parser, materializer, exporter) | verb + input → named output contract |
| Pure functions or values (math, texture, constants) | verb the effect, or a noun phrase naming the thing + what needs it |
| Registry, seam, index, protocol module | noun phrase naming the seam + what it decides |

**Never invent an analog.** If a reader would not know the analog from outside
this repo, it is not an analog — drop the slot.

## The slots

1. **Verb** — what the code does (`Emulate`, `Replay`, `Ray-cast`, `Yield`).
   Functions and methods: imperative (`Emulate`, not `Emulates`) — PEP 257.
   Modules may lead with a noun phrase (Go package comments do); stay consistent
   inside one file.
2. **Analog** — the real thing a reader already knows (`a live tracker`). Not the
   internal role (`stand-in`, `adapter`, `source`): team words, not pictures.
3. **Payload** — the actual messages or types (`PoseTick`, `Keyframe`,
   `Revision`). Not a category word (`posed-stream source`).
4. **Cadence** — the time or step shape (`one time step at a time`, `one PoseTick
   per frame`, `every stride`). For streams and replays this *is* the point.

Use different words than the identifier (Ousterhout). `def replay_run:
"""Replay a run."""` carries zero information.

## Hard rules for line 1

- One sentence, ends with a period.
- Fits one physical line, inside the project's line length (check
  `pyproject.toml` / `ruff.toml`; count the opening `"""`).
- Blank line before the body (PEP 257).
- No signature, no parameter names, no repeat of the function name (numpydoc).
- No spec section, ticket id, or citation. Those trail by a sentence or more.
- No title-case labels, no leading `Foo:` tag.

## The rest of the docstring

2–4 sentences, after the picture exists. Order: what this is **not**, where the
data comes from, who consumes it, the constraint that will bite. Rationale and
citations last (Diátaxis: reference informs action, explanation comes after).

Worked example — whole docstring, not just line 1:

```python
"""Emulate a live tracker feeding the posed-stream contract, one time step at a time.

``replay_run`` walks a recorded run dir (sim capture, phone upload, or a
finished live session) and yields the same messages a live tracker would:
one PoseTick per frame, plus a Keyframe every ``stride`` frames. There is
no tracker on this path. Poses come from traj_gt.txt, not from VIO.

``script_revisions`` wraps any source to mimic iSAM2's arrival-then-revise
shape for consumer tests: it perturbs keyframe poses at arrival and later
corrects them with Revision batches (spec section 4).
"""
```

Picture → payload → cadence → what it is not → source of truth → cite, last.

## Reject these leads

| Bad | Why |
|---|---|
| `File-replay posed-stream source + scripted synthetic revisions.` | Noun pile, no verb. Reader must decode the architecture before the sentence means anything. |
| `Stand-in for a live tracker (spec section 4).` | No verb, no payload, no cadence, and the cite is in line 1. |
| `The recorded adapter of the posed-stream contract:` | "Adapter" is a team word, not a picture. Title-case label ending in a colon. |
| `Replay the run by replaying the run dir.` | Same words as the identifier. Zero added information. |

## Already good — do not rewrite

These pass. They lack slots that do not apply. Leaving them alone is the correct
outcome.

| Lead | Why it passes |
|---|---|
| `Ray-cast RGB-D frames from an arbitrary triangle mesh, Isaac-free.` | Verb + payload. A renderer emulates nothing and has no cadence. |
| `Replica ingest: one scene dir -> the producer/ contract.` | One-shot transform: input → named output contract. |
| `Producer layer seam: what supplies a run's frame/sensor stream.` | Seam module. Noun phrase naming the seam is the honest shape. |

Rewriting a passing line to force all four slots is a failure of this skill, not
a use of it.

## Scope

- Applies to: module, class, and public-function docstrings; a leading comment
  that says what a file *does*.
- Not: commit messages, chat, inline comments, tests, private helpers.
- Touch only the docstring in scope. No drive-by rewrite of others in the same
  file, even when they fail the table above.

## Self-check

Before leaving a docstring:

1. You picked a shape from the table, and every slot in it exists in reality —
   no invented analog, no cadence on a thing without a clock.
2. A reader who does not know this repo's architecture can picture the subject.
3. Payload types are named, not hinted.
4. Line 1 is one sentence, on one line, inside the line-length limit, with no
   citation and no signature restating.
5. Wording differs from the identifier's own words.
6. You did not rewrite an already-passing docstring, or any docstring out of scope.

## Sources

PEP 257 (docstring conventions) · Google Python Style Guide §3.8 · numpydoc
style guide · Go doc comment guide · Ousterhout, *A Philosophy of Software
Design* ch. 13 · Google Technical Writing One · Diátaxis.
