---
name: writing-docstring-summaries-strict
description: >
  Use when auditing or rewriting docstring summary lines that already exist,
  when a summary may be stale or factually wrong, when one pass will touch many
  docstrings, or when the cost of an unnecessary edit is real (review noise,
  churn, introduced errors). Also use when the user says "docstring audit",
  "strict docstring style", "verb analog cadence", or asks whether a summary
  line is worth changing at all. Prefer this over writing-docstring-summaries
  when the risk is wrong or needless edits rather than awkward phrasing.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docstrings, Prose, Comments, Readability, Audit"
  category: "writing"
---

# writing-docstring-summaries-strict

Strict variant of `writing-docstring-summaries`. Same subject — the first line of
a module, class, or public-function docstring — with an edit gate before the
recipe, a truth rule above every style rule, and each rule tagged by how well it
is actually evidenced.

Work the sections in order. Do not skip to the templates.

## 1. Decide whether to edit at all

Edit a summary line only when at least one holds:

- You are creating the docstring.
- The summary is factually wrong, stale, or contradicts current behavior.
- The summary fails a check in §5.
- You are already editing that docstring for another necessary reason.

**An accurate, clear, compliant existing summary is already successful. Leaving
it unchanged is a correct outcome, not a skipped task.**

Template resemblance is not a reason to edit. Neither is a preferred sentence
shape, nor the fact that you were invoked.

Out of scope, always: other docstrings in the same file, neighbouring code,
tests, private helpers, inline comments, commit messages.

*[Agent] Coding agents show a measured bias toward editing when no change is
needed, and an explicit scope declaration plus a stated no-op success state is
the mitigation with the strongest current evidence. This section outranks every
style rule below.*

## 2. Classify the artifact

Classify from observable traits — base classes, decorators, whether it yields,
file location — not from taste.

| Kind | Observable trait |
|---|---|
| Time-shaped stream, emulator, replay | yields/iterates, has a step or tick, substitutes for a live producer |
| One-shot transform | ingest, parse, convert, export; runs once, returns or writes a result |
| Pure-function library | free functions over values, no I/O, no state |
| Registry, seam, dispatch, protocol | maps names to builders, defines an interface, selects an implementation |
| Data class / state object | dataclass, NamedTuple, TypedDict, plain state carrier |
| Other or unclear | none of the above fits cleanly |

## 3. Write the summary

Positive recipe per kind. Every slot is conditional — include it when the fact
exists and the caller needs it, otherwise leave it out.

| Kind | Recipe |
|---|---|
| Time-shaped stream | role it fills + payload/contract when useful + cadence or ordering |
| One-shot transform | transformation: meaningful input → named output contract. No cadence. |
| Pure-function library | module: noun-led domain and purpose. Function: the action and what distinguishes it. |
| Registry / seam | the architectural role, and what it connects, selects, or exposes. Not a time process. |
| Data class / state object | noun-led: what state it represents; ownership or lifecycle if non-obvious. |
| Other or unclear | a plain factual summary. **Force no template.** |

### Role, not metaphor

A **role** is a position the code literally occupies at an interface. A
**metaphor** is a resemblance you supplied.

- `Emulate a live tracker feeding the posed-stream contract, one time step at a time.`
  Role. The module is a drop-in behavioral substitute at the tracker's interface,
  and `posed-stream contract` is terminology callers need.
- `Behave like a conveyor belt for poses.`
  Metaphor. It imports buffering, ordering, and lossiness the code never promised.

Never invent a role to fill a slot. If the code substitutes for nothing, the
slot does not exist.

*[No study found] Analogy in code summary lines has never been tested. Adjacent
analogy research shows benefit depends on structural alignment, and that partial
mappings create false inferences. Treat any analogy as optional and load-bearing
only when literally true.*

## 4. Truth and information gain (hard rules)

**Truth.** Do not state a role, payload, cadence, ordering, unit, guarantee, or
side effect that the implementation and interface do not support. When unsure,
omit the slot. An omitted fact is recoverable by reading the code; a false one
teaches the wrong model and survives review.

**Information gain.** The summary must add at least one fact a reader cannot get
from the name and signature — role, contract, invariant, ordering, unit, side
effect, or intent. Repeating the entity's own name is allowed. Restating *only*
the name is not.

```python
def replay_run(...):
    """Replay a run."""                    # no gain: expands the name, nothing else
    """Yield one PoseTick per recorded frame; poses are ground truth, not tracked."""
```

*[Repository + Practitioner] Misleading and stale comments are the most
consistently condemned documentation defect in comment-quality studies and
practitioner surveys, and code-comment inconsistency is well documented in
large-scale history mining. Comments that merely restate code are the most
frequent smell observed. These are the best-evidenced rules in this file.*

## 5. Deterministic checks

House convention. Check them, but never trade a truth violation for one of these.

- One sentence.
- One physical line, within the project's configured line length (read
  `pyproject.toml` / `ruff.toml`; count the opening `"""`).
- Ends with a period.
- Multiline docstring has exactly one blank line after the summary.
- No signature restated, no parameter list.
- No citation, spec section, ticket id, URL, or markup link.
- No title-case label and no leading `Foo:` tag.
- Functions and methods: imperative mood, if the file already uses it.

*[Convention] No comprehension study supports imperative mood, any specific
character cap, or verb-lead over noun-lead; official conventions across Go,
Rust, Swift, Kotlin, Java, and C# actively disagree on all three. Ruff enforces
several of these (D400 period, D205 blank line, D402 signature, D401 mood) and
notes D401 is convention-dependent. Keep them as house style. Do not defend them
as science.*

## 6. Examples

One per kind, so no single sentence shape becomes the pattern to copy.

```python
# stream / emulator
"""Emulate a live tracker feeding the posed-stream contract, one time step at a time."""

# one-shot transform
"""Materialize a public-dataset sequence into the producer/ keyframe store."""

# pure-function module
"""Procedural surface texture for synthetic captures."""

# pure function
"""Compose two rigid transforms in frame order."""

# registry / seam
"""Producer layer seam: what supplies a run's frame/sensor stream."""

# data class
"""Per-frame state shared between tracking and mapping stages."""
```

**Already good — leave unchanged:**

```python
"""Ray-cast RGB-D frames from an arbitrary triangle mesh, Isaac-free."""
```

Verb and payload, no role and no cadence, because a renderer substitutes for
nothing and runs on no clock. Complete as written.

**Rejected:**

| Line | Kind | Fault |
|---|---|---|
| `Emulate a switchboard feeding the adapter contract, one lookup at a time.` | registry | Invented role, invented cadence. Slot-filling. |
| `Yield frames in timestamp order.` on a source with no ordering guarantee | stream | False. Truth beats a well-shaped sentence. |
| `File-replay posed-stream source + scripted synthetic revisions.` | stream | Noun pile. No verb, no cadence, reader decodes architecture first. |
| Rewriting an accurate summary to match an example above | any | §1. Not a reason to edit. |

## 7. Final pass

Answer each separately. Do not answer them as one judgment.

1. Did §1 authorize this edit at all? If no — revert it.
2. Is every fact in the line supported by the code you read?
3. Does the line add at least one fact beyond the name and signature?
4. Does the kind you chose in §2 match an observable trait, not a preference?
5. Are all conditional slots you used real — no invented role, payload, or cadence?
6. One sentence, one line, inside the line-length limit?
7. Period at the end, blank line after, no citation, no signature?
8. Did you leave every other docstring in the file untouched?

*[Agent] Models drop constraints from compound instructions at measurable rates;
decomposing a policy into separately checked predicates and running an explicit
compliance pass recovers part of that loss. Answer the eight one at a time.*

## Evidence classes used above

| Tag | Meaning |
|---|---|
| Repository / Practitioner | Mined histories, comment corpora, or practitioner surveys |
| Agent | Empirical LLM instruction-following and coding-agent behavior |
| Convention | Official language, style-guide, or linter semantics — no demonstrated human benefit |
| No study found | No direct empirical test of this prescription exists |

## Sources

PEP 257 · Google Python Style Guide §3.8 · numpydoc · Go doc comment guide ·
rustdoc, KDoc, DocC, Javadoc summary semantics · Ruff D205/D400/D401/D402 ·
Ousterhout, *A Philosophy of Software Design* ch. 13 · Diátaxis · comment-smell
and code-comment-inconsistency literature · 2026 coding-agent scope and
action-bias studies.
