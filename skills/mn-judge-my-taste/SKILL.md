---
name: mn-judge-my-taste
description: Judge my taste from how I worked with you. Read my prompts, my pushback, my own drafts and what I left alone, then report which habits to keep and which to criticize, each with the evidence and what it cost. Use when I say "judge my taste", "extract my taste", "what did you learn about how I work", "criticize how I worked", "what are my bad habits", "retro on me", or ask for feedback on me and not on the code. Also use when I point at a file, a PR or a transcript and ask what it says about my taste. Not for a code review (code-review) and not for saving one preference I just stated (memory).
argument-hint: "[this session (default), or files, a PR, a transcript]"
---

# Judge my taste

Tell me what my choices say about my taste, and whether that taste is good. I want the good parts named
so they can become rules. I want the bad parts criticized, even when they are what I asked for. A report
that only describes me, or only agrees with me, is a failed report.

Scope: $ARGUMENTS

With nothing passed, the scope is this conversation.

## What counts as taste

Taste is a choice I made when another choice was open. Look for it in six places:

| Place | Example |
|---|---|
| What I asked for | "show me the changes" before "apply" |
| What I pushed back on | "is that added complexity?" |
| What I renamed or reworded | `rows` to `sequence` |
| What I took without a question | a patch, a number, a label |
| What I left alone | a defect you put a number on, and I never came back to it |
| What my own draft looks like | names, density, comments, stale text |

Silence is evidence. The fourth and fifth rows are where bad taste hides, because nothing I said marks them.

A fact about me is not taste (my OS, my project). A mood is not taste. A choice that I had no room to
make differently is not taste: say so and leave it out.

## How to judge

- **Evidence or nothing.** Each line quotes my words as I typed them, or names a file and line, or gives
  a number from the session. If you cannot point at it, drop the line.
- **Judge by consequence.** Good taste made the result more true, simpler, or cheaper to change. Bad
  taste cost turns, hid a defect, caused a revert, or made the work harder to read. Give the cost when
  you can count it: turns, millimetres, lines, a revert.
- **Different from your default is not bad.** If I chose against your habit and nothing went wrong, that
  is not a criticism. If it went well, it is a keep.
- **What I want can be wrong.** When I ask for something and it is bad taste, say it is bad taste and why.
  Do not turn it into a preference to respect.
- **Find the contradictions.** Set what I demand of you next to what I accept in my own draft. A rule I
  apply to your work and not to mine is the most useful line in the report.
- **Keep my faults and yours apart.** If I looked sharp because I caught your mistake, say that the
  mistake was yours. Do not list your error as my flaw, and do not soften a criticism of me by blaming
  yourself.
- **Mark the sample.** One session is small. Say "once" or "three times". With the ledger, say "also on
  2026-11-20". Do not build a personality from one message.
- **No praise.** A keep is a rule that a later session can apply, written as a rule. It is not a compliment.
- **Rank criticism by cost**, the most expensive first.

## The report

Answer in chat, in this order. Keep each line to one or two sentences.

1. **Keep.** A table: the taste as a rule, then the evidence.
2. **Criticize.** A numbered list, most costly first. Each item: the habit in bold, the evidence, the
   cost, and a **counter-move**: what you should do the next time you see me do it.
3. **Pattern underneath.** Two or three sentences that explain several lines above at once. Skip it if
   no pattern is there.
4. **Where it goes.** For each keep, the place that would make it stick: one of my skills (name it), a
   `CLAUDE.md`, a memory, or nowhere. One line each.

Then stop. Do not offer to fix the bad habits in the current work unless I ask.

## The ledger

`ledger.md` in this skill's folder holds what earlier runs found. The folder is a git repo that I pull
on every machine, so the ledger follows me.

- **Before you judge**, read it. An item you see again is stronger evidence than a new one: say so, with
  the earlier date.
- **A new finding that contradicts the ledger** is worth a line of its own: my taste moved, or it is not
  consistent.
- **After the report**, ask once which lines to save. Write only those. For a line already there, add the
  date and raise its count. Never delete a line: if I reject one, mark it rejected with the date and my
  reason.
- Keep quotes short, and keep project secrets and other people's names out of it.

A ledger entry has this shape:

```markdown
### Labels must match what the code does
- Kind: keep
- Seen: 1 (2026-11-20, b2_ws mj4)
- Evidence: asked "are we using TSR?" three ways until the answer was "no, one hard-coded axis".
- Counter-move or home: mn-code-shape
```

## Other scopes

- **Files or a PR.** The evidence is the artifact alone: names, structure, comments, what is stale, what
  the history shows I changed my mind on. Say that no interaction was seen, so the "took without a
  question" and "left alone" rows are empty.
- **A transcript.** Same as a session. Quote with the turn or the line.
