---
name: mn-paper-rewrite
description: >
  Rewrite a research paper, or one method from it, in the order the data
  flows, not the order of the paper's claims. Three depths. Rewrite: one
  illustrated page with a system diagram, a contract per stage (inputs,
  outputs, shapes, units), every derivation step by step, a ledger that
  accounts for every quantity, and a critical read of the evidence. Trace:
  the mechanism in chat on one running example. Gist: a short plain-English
  notes file. Use it whenever the user points at a paper (arXiv id, PDF,
  main.tex, a paper's repo) and wants to understand it, says a paper is hard
  to read or follow, asks "how does this paper actually work", "what is it
  learning", "where does X enter the loss", "explain the derivations", "plain
  notes", "in one breath", "paper rewrite", or restates a pipeline ("so
  basically they ...") to test it, even with no depth named. For a concept
  with no paper behind it, use mn-explaining-new-topics. For a course on a
  whole topic, use mn-grounded-primer. To run a paper's code, use
  paper-playground.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Papers, Explanation, Derivation, Diagrams, Notes, Mechanism"
  category: "writing"
---

# mn-paper-rewrite

A paper is written for reviewers. It orders its text by claim, compresses its
derivations, and leaves out what an expert finds obvious. I read a paper to
rebuild the method. So rewrite it for that: in the order the data flows, with
nothing appearing from nowhere, and with every statement traceable to the
source.

## My background

Read `~/.config/skills/background.md` first if it exists. It says what I
work on, which tools I use, and what I know and do not know yet. Pitch the
answer to it. If the file is missing, assume an engineer who knows basic
linear algebra and calculus, and define each term at its first use.

- I understand by tracing one concrete example end to end, in the order the
  data flows, with real numbers at each step.
- I often restate what I think happens. If I am right, say so plainly. If I
  am wrong, correct only the part that is wrong.
- Put each equation next to the concrete case, define every symbol, and name
  the file or function that does that step.
- Diagrams, tables and interactive visuals help me more than long prose. Give
  commands as copy-paste blocks.
- Short lines and short paragraphs. Answer my exact question first, without
  padding. When you offer options, recommend one.

## Pick the depth

| Depth | I asked for | You give | Read |
|---|---|---|---|
| **gist** | notes, plain English, "in one breath", a quick judgement | a notes file of about 150 lines | `references/gist.md` |
| **trace** | "how does it work", one mechanism, a restatement to check | a walkthrough in chat, ten rungs | `references/trace.md` |
| **rewrite** | a rewrite, a page, all the derivations, "hard to follow", the whole paper | one page, saved and published | the rest of this file, then `references/page.md` |

When I name no depth: a question gets a trace, and a paper handed over with
"I cannot follow this" gets a rewrite. A rewrite of one section is fine; say
which part you cover. Say in one line which depth you picked, then start.

## What every depth shares

**Read all of the source.** The method, the algorithm boxes, the captions, the
footnotes, the appendix and the supplement. Prefer the LaTeX source (arXiv
`e-print`): its equations are exact, and a PDF read can drop a subscript. On
a PDF, look at equation-heavy pages as images when the extracted text looks
garbled. Read the official code when it exists, and note its commit. The code
holds the glue that papers leave out: truncated gradients, loss terms that
are switched off, clamps, integer casts. When paper and code disagree, follow
the code and say so with `file:line`. Keep the paper's own statement next to
it, also when the code is only more exact ("tens of thousands of springs" in
the paper, 27,655 in the released data): I check the page against the paper.
Unpack a download into its own empty folder.

**Follow one hop.** When the method leans on a result from another paper
("following [12]"), read that part of [12] and state the result here. I
cannot follow a derivation whose first line lives in a paper I have not read.
Stop after one hop, and say what you read.

**Carry one running example.** Take the paper's own case with its real
numbers: point counts, parameter counts, time steps, results. Use it at every
stage. Most papers print results, not what happens inside one case. Fill the
inside from the nearest real source: the released data, logs and configs
first, then a small run of your own that follows the paper's setup. Say at
each number which source it has. A number from your own run stays `mine`
everywhere it appears, also in the one-breath chain and the restate check.
Name every setting you had to choose, and set the run against a number the
paper prints. When the two disagree, say so: your run must never read as the
paper's result.

**Mark where each statement comes from.** Three marks:

- `paper`, with a locator: section, equation, figure, table, appendix.
- `code`, with `file:line`.
- `mine`: a step you filled in or an inference you drew. Add `checked` and
  how, or `unchecked`.

A rewrite that reads smoothly hides the seam between what the authors wrote
and what you added. The marks keep that seam visible, so I know what to
trust and what to verify. Three rules keep a mark honest:

- **A mark covers what its source says at that place, and no more.** The
  reason for a step, the cause of a result, or how an experiment was run is
  yours unless the source writes it. Split the sentence and mark your half
  `mine`. A fact that only the code gives takes a `code` mark, not the
  paper's.
- **`checked` means the check would fail if the statement were false.** A
  count, an identity or a gradient can be checked. A check that recomputes
  the formula it guards proves nothing. A cause ("the baseline fails because
  of its iteration cap") is not checked by arithmetic: it stays `unchecked`
  until you run the experiment that could refute it.
- **I can rerun or open what a mark names:** a function of the checks file,
  a `file:line`, a place in a paper. A test you ran once somewhere else goes
  into the checks file, or the mark says `unchecked`.

Mark every paragraph, list item, glue fact, derivation step and row of
numbers. The lede, the one-breath chain and the takeaway lines need no mark,
so they may only repeat what the marked text under them says. Write them
last, from the finished chapters.

**Do not smooth over a gap.** Never invent a number. Never turn a hedged
claim into a flat one. When the paper does not state a detail, write "not
stated", then what the code does, or your guess marked as a guess.

**Hunt the glue facts.** A glue fact is an identity or link that experts
leave unsaid: "the first 1,630 particles are the tracked points", "the hand
acts only through springs built at frame 0". State each one at the place
where it is first needed. These are where I get stuck.

**Read critically.**

- Quote a claim before you judge it. A claim that you restate in stronger
  words and then mark down is your overclaim, not the paper's.
- Call out wording or notation that misleads, and say what actually happens.
- List what the paper leaves unsaid that I need to reproduce it: engine, mesh
  size, constants, training time.
- Compare the numbers with real-world values. Say when a number is a fitted
  knob, not a physical constant.
- Run the pseudo-code as printed in your head. Flag bugs.
- Flag evaluation on the fit data, too many unknowns for the data, weak
  baselines, and confounds (two causes that give the same result).

**Answer my restatements.** When I write "so basically they ..." or ask a
short follow-up, start with "Yes", "Yes, with N corrections" or "Not quite".
Then fix one wrong assumption at a time, in the order of the data flow, on
the same running example.

## Rewrite: the steps

1. **Fetch.** The LaTeX source or the PDF, the supplement, and the code at a
   pinned commit. Record the arXiv version and the commit; the page prints
   them.
2. **Inventory.** List every section, numbered equation, algorithm, figure
   and table, and every symbol with the place that defines it. These rows
   become the coverage table and the ledger. Do this before any prose: it is
   what makes "the whole paper" checkable.
3. **Skeleton first.** Cut the method into stages in data-flow order. For
   each stage, fill its contract: what goes in, what comes out, which knobs
   it has, each with shape and unit. Fill the ledger. Then run the
   accounting check below. A contract you cannot fill is a stage you do not
   understand yet: go back to the source or the code, and do not cover the
   hole with prose.
4. **Write the stages.** One chapter per stage, with the parts that
   `references/page.md` lists.
5. **Check the derivations** by the rules below.
6. **Evidence, gaps, rebuild sheet.** What each claim rests on, what the
   paper leaves out, and what I need to build it.
7. **Cold read.** Give one fresh subagent the page and the source, with the
   brief in `references/page.md`. It lists contradictions, numbers it cannot
   find, marks that claim more than they cover, terms used before their
   definition, and steps it cannot follow. Fix what it finds. One pass, not a
   loop. Pick its model by how much math the paper carries.
8. **Lint, look, publish.** Run `scripts/check_page.py PAGE.html` until it
   prints no error; fix each warning or explain it in the report. Run
   `scripts/render_check.py PAGE.html`: it loads the page at desktop and
   phone width and saves screenshots. Open the screenshots. Save and publish
   as `references/page.md` says.
9. **Report.** What the page covers, which numbers come from your own run,
   how many steps are `mine, unchecked`, and the open questions.

## The accounting check

Every quantity a stage reads must come from somewhere: an earlier stage made
it, or the ledger lists it as an input, a given, a hand-set knob or a learned
parameter. Every quantity a stage makes must be in the ledger. The ledger has
seven kinds:

| Kind | Meaning |
|---|---|
| `input` | measured or observed data, given at run time |
| `given` | fixed knowledge: a calibration, a model, pretrained weights, a constant |
| `hyper` | a knob set by hand |
| `learned` | a parameter fitted in training |
| `solved` | an unknown estimated at run time: a state, a pose, a latent |
| `derived` | an intermediate that a stage computes |
| `output` | what the method returns |

This check is where a paper's holes show: a symbol that is never defined, a
weight with no stated value, a tensor whose size no stage sets. The lint
script runs the check on the page's tables.

## Derivations

A derivation is the part of a paper I most often cannot follow, so it gets
the most care.

- Say what is being derived and why it is needed, before the first line.
- One move per step, and name the move: "chain rule", "the trace is cyclic",
  "drop the term that does not depend on θ".
- Write the shape and the unit of every term once. A mismatch is your misread
  or the paper's typo; find out which, and say it.
- Fill every step the paper skips ("it is easy to show"). Mark these `mine`.
  A step the paper prints takes the paper's mark, so every step shows whose
  it is.
- Check what you filled: a few lines of numpy on a small random instance, a
  finite difference for a gradient, sympy for algebra. Test the step's own
  equality, not a weaker consequence of it. Save the checks in one file next
  to the page and name the function in the mark.
- For a result imported from another paper: state it, give two lines on why
  it holds, and cite the place. Do not re-derive the other paper unless I
  ask.
- When you cannot reproduce a step, write "I could not reproduce this step"
  and show where it breaks. A paraphrase of the paper's sentence is not a
  derivation.
- The derivation that the method hinges on stays open on the page. Routine
  algebra goes in a closed fold, one click away.

## Self-check

The two scripts test the page's structure and its rendering. These points
they cannot test:

1. The one-breath chain alone tells me what goes in, what comes out and the
   one idea.
2. Every stage uses the running example, and each of its numbers says
   whether the paper, the released data or your own run gives it.
3. No mark claims more than its source says, and no number is invented.
4. Every numbered equation, algorithm, figure and table of the paper is in
   the coverage table, at the place that holds its content.
5. The evidence table quotes each claim. The gaps section names what is
   unsaid, what is buggy and what can fake the result.
6. The report gives the count of unchecked steps.
