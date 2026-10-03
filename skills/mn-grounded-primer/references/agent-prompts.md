# Agent prompts

Four prompts. Fill the angle-bracket placeholders. Send each as written; the
sentences about reading files first, reporting "claims to check", and never
touching files outside the folder came from failures on the first run.

Placeholders used below:

- `<TOPIC>`: the subject.
- `<FOLDER>`: absolute path of the primer folder.
- `<ANCHOR>`: the repo path, library, or target problem, plus the documents
  that hold its measured numbers.
- `<READER>`: one or two sentences on background, including the exact words
  the user used ("I cannot understand the low-level math").
- `<PYTHON>`: the command that runs a script, for example
  `cd <repo> && env -u PYTHONPATH pixi run python <script>`.
- `<CHAPTERS>`: the chapter numbers, file names and a paragraph of required
  content for each chapter this writer owns.
- `<CANONICAL FORMS>`: equations that more than one chapter writes, in the
  one form all chapters must use, with the source line they match.

## 1. Chapter writer (subagent_type: "fork", two or three chapters each)

```
You are the fork writing primer chapters <NN, NN> under <FOLDER>. Execute
directly, do not re-delegate. Write only these files, nothing outside
<FOLDER>:
<list of file paths>

Audience: <READER>. Assume vectors, matrices, derivatives, Python. Build
everything else from scratch. Simple English, pragmatic register: short
sentences, active voice, define every term at first use, no em-dashes, no
contractions. Math in Markdown with $...$ and $$...$$. Each chapter 1,500 to
3,500 words.

Follow the eight-section chapter shape exactly (why this matters here,
concepts from scratch, pen-and-paper derivation with a tiny worked example
in real numbers, "in our code" with file:line references you verified by
reading the file, "in other tools", one numpy snippet under 50 lines that
prints the worked numbers, three exercises with answers, further reading as
names only). Where chapters share an equation, use this form and these
symbols: <CANONICAL FORMS>.

Anchor and sources for measured numbers: <ANCHOR>. Quote a number only with
its conditions and its source document. Label anything else "estimate" or
"not measured".

Chapter contents:
<CHAPTERS>

For any claim about a tool that is not the anchor, cite a primary source
(official docs, changelog, source tree), not the anchor repo's notes about
that tool. Those notes go stale.

Before writing, read the anchor files so every file:line is exact. Report
back: the file paths, five bullets per chapter of claims a reviewer should
check, and any claim you were not sure about.
```

## 2. Researcher (subagent_type: "general-purpose", fresh, web tools)

```
Build a verified, curated resource list for a from-scratch primer on
<TOPIC>, and download the open-access papers. Write <FOLDER>/resources.md
and save PDFs into <FOLDER>/refs/. Modify nothing else.

Context: <READER>. The primer chapters are: <chapter list with one line
each>.

Task.
1. For each chapter find 3 to 6 resources: one textbook or course notes, one
   or two primary papers, one lecture video series when a good one exists,
   the official documentation page where relevant. Prefer free. Verify every
   URL by opening it (WebFetch, or the arXiv tools for arXiv ids). Do not
   list a link you did not open. For each: title, authors, year, type, free
   or paid, URL, which sections or lectures, estimated hours, one sentence on
   why it fits that chapter.
2. Seeds to verify, and replace if they fail: <seed list>.
3. Download open-access PDFs into refs/ with short slug names. Only arXiv,
   author-hosted preprints, open course notes. Never paid textbooks. Check
   each file with `file` and a first-page text extraction, and keep only real
   PDFs over 50 KB. Mark each downloaded file in resources.md.
4. Write resources.md in simple English: intro, one section per chapter with
   a table, "one week, about 20 hours" and "one month" plans, the list of
   downloaded files with sizes. No em-dashes, no contractions, sentences
   under 25 words.

Report back: the path, the refs/ listing with sizes and total, how many URLs
you verified, and every seed you dropped or changed, with the reason.
```

## 3. Verifier (subagent_type: "general-purpose", model: "opus")

```
You are the verification pass for <FOLDER>. Chapters 01 to NN and README.md
exist. Do not touch resources.md or refs/. Modify nothing outside <FOLDER>.

Python: <PYTHON>.

Writing rules for prose you add: simple English, sentences under 25 words,
active voice, no contractions, no em-dashes, define a term at first use.

Tasks, in order:
1. Exercises. Copy each chapter's snippet into exercises/exNN_<slug>.py with
   a two-line docstring (chapter, section, numbers it must print). Run every
   script. Where script and text disagree, re-derive to find which is right,
   fix the other, record the fix. Make each script assert the numbers the
   chapter states, so a later drift fails loudly. Write exercises/README.md
   and run_all.sh (exits nonzero on any failure; test that).
2. Cross-chapter consistency. Read all chapters. Then:
   a. Canonical forms: <CANONICAL FORMS>. Make every chapter match.
   b. Items from the writers' "claims to check" lists: <paste them>.
   c. Re-grep every file:line reference in every chapter and fix any that is
      off.
   d. Every "see chapter NN" must point at a chapter that covers the thing.
   e. Every "not measured" and "estimate" label stays.
   f. Where two chapters derive the same quantity under different conditions,
      state both values with their conditions in both chapters.
3. Glossary. Write 00-glossary.md: every defined term, one line, alphabetical,
   with the defining chapter. Add a one-sentence definition in the chapter
   where a term is used but never defined.
4. README. Confirm every chapter file name in the table exists. Add the
   pointer to exercises/README.md and run_all.sh.
5. Lint. Find the simple-english lint script
   (`find ~/.claude -name ste_lint.py`) and fix prose hits (sentences over
   25 words, contractions, "should", "may"). Ignore hits inside math or
   code.

Report back: scripts with pass or fail, every text fix (chapter, section,
old, new, why), how many file:line references were off, the glossary count,
anything unresolved.
```

## 4. Reviewer (subagent_type: "general-purpose", model: "opus")

```
You are the final adversarial reviewer of <FOLDER>. Review README.md,
00-glossary.md, every chapter, resources.md, exercises/. Do not modify
anything outside <FOLDER>. Do not touch refs/.

Purpose of the primer: <one paragraph: topic, anchor, reader, the specific
question the user asked that the primer must answer plainly>.

Ground truth: <ANCHOR files and documents>. Python: <PYTHON>.

Review on four axes, adversarially. Try to break each claim.
A. Mathematical correctness. Re-derive every displayed derivation on paper
   or in a scratch numpy session. Sign conventions, factors of 2, units. Fix
   errors in text and script, re-run the script, record the fix.
B. Fidelity to the anchor. Every file:line points at what the text says
   (grep each). Every measured number exists in a source with the same
   conditions. Every statement about what the code does matches the code.
   Keep "not measured" and "estimate" labels.
C. Fidelity about other tools. Verify against primary sources (official
   docs, changelogs, source trees), not against the anchor repo's own notes,
   which can be stale. Relabel an inference as an inference.
D. Pedagogy. Read as the intended reader. Terms defined before use, no
   unresolved forward references, no skipped step, every example has
   numbers, the final "what we did versus the alternatives" chapter lands,
   the user's specific question is answered plainly. Apply small fixes.
   List larger ones without applying them.

Writing rules for prose you add: simple English, sentences under 25 words,
active voice, no contractions, no em-dashes.

Finish by running exercises/run_all.sh.

Report back, in order: (1) verdict in two sentences; (2) errors fixed,
chapter + section + was + now, most serious first; (3) inferences relabeled;
(4) pedagogy fixes applied; (5) larger suggestions not applied; (6) what you
could not verify and what it would take; (7) run_all.sh result.
```
