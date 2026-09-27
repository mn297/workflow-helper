---
name: mn-writing-plain-paper-notes
description: >
  Use when the user asks for plain-English, layman, or "explain it like a
  labmate" notes on a research paper, or wants to understand a paper well
  enough to rebuild it. Also use when the user says "plain notes", "layman",
  "in one breath", "what does this paper actually do", or points at a paper
  source (arXiv dir, main.tex, PDF) and asks for notes. Produces a short,
  gist-first, critical notes file. For a thorough chat explanation of a
  concept, use mn-explaining-new-topics instead.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Papers, Notes, Explanation, Prose, Readability"
  category: "writing"
---

# mn-writing-plain-paper-notes

Goal: after one read I can explain the paper to a labmate and start rebuilding
it. Not a tutorial, and not a section-by-section summary.

Me: robotics/sim engineer. I know the basics, but not this subfield's jargon.

The voice rules below win over any general docs register (for example
simple-english) for this notes file. Contractions and whiteboard tone are
intended.

## Before writing

1. Read the full source, not only the abstract: `main.tex` (or the PDF),
   algorithms, tables, figure captions, appendix.
2. If the paper sits in a project repo, read the nearby plan or spec so the
   "Our version" section maps onto real code. If there is no project
   context, leave that section out.
3. Save as `plain-english-notes.md` next to the project's plan for that paper,
   unless the user names another place.

## Voice

- Talk like a colleague at a whiteboard. Short sentences, contractions,
  everyday verbs (push, pull, tweak, nail down).
- Keep the real term so I can search it, but give its plain meaning in a few
  words in the same line: "Laplacian contraction squeezes the cloud down to a
  thin centre line (the branch's bones)." Do not stop to teach it.
- Give every abstract step a physical picture: "closer control point = more
  say", "try, compare, try again".
- Arrows and fragments are fine in pipelines and step lists. Everywhere else,
  write plain sentences.

## Shape

1. Open with "The whole thing in one breath": the full method as one arrow
   chain (A → B → C → D), then split it into its 2–3 halves. If I can skip a
   part, name it and say why in one line.
2. One section per idea. Use short plain headers ("Why force, not position"),
   not numbered questions.
3. Start every section with one bold sentence that is the takeaway. Details
   come after it.
4. Procedures are numbered steps. Each step is a bold label plus 1–2
   sentences.
5. Math: only the equation that IS the method (for example, the loss). Add one
   back-of-envelope formula as a gut check when it shows why the method works
   (for example, cantilever tip deflection F·L³/(3·E·I)).
6. Use tables for side-by-side choices. Use a small ASCII sketch when the
   position of things matters.
7. End with "Gotchas" and "Our version" (how it maps onto my project, and
   what we do differently).

Typical skeleton:

```markdown
# <Paper topic>: Plain-English Notes

## The whole thing in one breath
## Step 1: <first half>
## Step 2: <second half>
## Why <key design choice>
## <The part the paper explains badly>
## What comes out, and the gotchas
## Our version
```

## Read critically

- Point to where each claim comes from (Fig. 3, Table I, Algorithm 1,
  Sec. IV).
- Call out wording or notation that misleads, and say what actually happens.
- List what the paper leaves unsaid that I need to reproduce it
  (engine, mesh size, constants).
- Compare the numbers with real-world values ("1,000× below green wood"). Say
  when a number is a fitted knob, not a physical constant.
- Run the pseudo-code as printed in your head. Flag bugs.
- Flag: evaluation on the fit data, too many unknowns for the data, and
  confounds (two causes that give the same result).

## Length

The whole paper in about 150 lines. Cut anything I do not need to rebuild or
judge the method. If a sentence needs a second read, rewrite it shorter.

## Example

Paper: "The parameters θ are optimized via a derivative-free Nelder–Mead
simplex minimizing trajectory discrepancy."

Plain: "Nelder–Mead picks a new θ. No gradients, so it's just try, compare,
try again. Every try is a full sim run."

## Self-check

1. The one-breath chain alone tells me what the method does.
2. Every section opens with a bold takeaway sentence.
3. Every kept term has a plain meaning next to it on first use.
4. Every number and claim points to a figure, table, section, or algorithm.
5. Gotchas name what is unsaid, what is buggy, and what can fake the result.
6. The file is about 150 lines, not a section-by-section retelling.
