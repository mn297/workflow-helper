---
name: mn-grounded-primer
description: >
  Use when the user wants to learn a topic from scratch as a multi-chapter
  tutorial folder: a learning plan, a "basics tutorial series", a curriculum,
  a study guide, or a primer, with pen-and-paper math, runnable exercises, a
  verified resource list and downloaded papers. The topic is anchored on
  something the user owns or wants to adopt: a repo, a solver, a paper, or a
  library to learn (FEM with FEniCS, factor graphs with GTSAM, and so on).
  Also use when the user says "I cannot understand the low-level math",
  "teach me X from basics", "learning plan", "tutorial series", "from
  scratch, each concept", "deep research good resources and collect them to a
  folder", or "what did we do versus engine Y". Make sure to use this skill
  even when the user names no folder and no chapter list; propose both.
  For one chat explanation use mn-explaining-new-topics. For notes on one
  paper use mn-writing-plain-paper-notes.
compatibility: claude-code
metadata:
  tags: "Teaching, Tutorial, Curriculum, Math, Subagents, Research"
  category: "writing"
---

# mn-grounded-primer

A grounded primer is a folder of 8 to 12 chapters that teaches one topic from
scratch. "Primer" means a ladder: each chapter adds one concept and uses only
earlier chapters. "Grounded" means every chapter ties the concept to one
artifact the reader owns, with a `file:line`, a measured number, and a snippet
that reproduces that number. A survey is not a primer. Paper notes are not a
primer. The output is a folder, never a chat answer.

Reference instance: `/home/john/tree_physics/tutorial/` (tree-sim versus
Newton, MuJoCo, Isaac Lab, built 2026-10-02). Read its `README.md` and one
chapter before the first run on a new topic, to see the shape.

## Me

Robotics and simulation engineer. I build things with help, then want to
understand the mathematics under them. Strong at code, weak at the derivation
chain. Assume vectors, matrices, derivatives, Python. Build everything else.

## 1. Pin down five inputs, then move

Take these from the conversation. Propose any that are missing and proceed.
Ask at most one question, and only when two readings lead to different
folders.

| Input | Default when missing |
|---|---|
| Topic | The thing the user named |
| Anchor | A repo path the user owns that uses the topic. If none, one target problem solved in the simplest library for that topic, then mapped to the library the user wants to learn (example: FEM anchor = a cantilever in scikit-fem, then the same problem in FEniCSx) |
| Reader background | The "Me" section above |
| Folder | `<repo>/tutorial/` if the anchor is a repo, else `~/tutorials/<topic-slug>/` |
| Ladder | Propose 8 to 12 chapters, one concept each. Chapter 1 is the mathematical object the reader cannot skip. The last chapter is "what we did versus the alternatives" |

The anchor matters most. Without it the writers produce textbook summaries
with no `file:line` and no measured numbers, and the reader cannot check
anything.

## 2. Folder layout

```
<folder>/
  README.md               learning plan: chapter table with the question each answers and hours, how to use a chapter, one-paragraph story
  00-glossary.md          every defined term, one line, alphabetical, with chapter number
  01-<slug>.md ... NN-<slug>.md
  resources.md            verified links per chapter, one-week and one-month plans, list of downloaded files
  refs/                   open-access PDFs only, slug names, each over 50 KB and a real PDF
  exercises/              exNN_<slug>.py per chapter snippet, README.md, run_all.sh
```

## 3. Chapter shape

Every chapter follows `references/chapter-template.md`. The eight sections, in
order: why this matters here, concepts from scratch, pen-and-paper derivation
with a tiny worked example in real numbers, "in our code" with verified
`file:line`, "in other tools", one numpy snippet under 50 lines that prints
the worked numbers, three exercises with answers, further reading as names
only. Length 1,500 to 3,500 words.

Why fixed: the verifier extracts the snippet of every chapter by its section
name, and the reader learns to find the derivation in the same place each
time.

## 4. Workflow

Run it in four waves. The prompts are in `references/agent-prompts.md`; fill
the placeholders and send them as written, they encode the lessons of the
first run.

1. Write `README.md` yourself first, with the final chapter table. The
   writers and the verifier read the chapter list from it.
2. Fan out in one message:
   - Chapter writers. Two or three chapters each. Use `subagent_type: "fork"`
     so each writer inherits the conversation, including every repo fact
     already established. Tell each writer to read the anchor files before
     citing a line, and to end its report with "claims a reviewer should
     check". Those lists feed wave 3.
   - One researcher. A fresh `general-purpose` agent with web tools. It
     verifies every link by opening it, downloads only open-access PDFs,
     checks each file is a real PDF over 50 KB, never downloads paid books,
     and writes `resources.md`.
3. Verifier, after all writers report. One fresh agent with
   `model: "opus"` because it writes scripts (forks ignore the model
   override). It extracts snippets to `exercises/`, runs them, fixes text or
   script where they disagree, reconciles the cross-chapter items you list
   from the writers' reports, re-greps every `file:line`, builds the
   glossary, updates `README.md`, and runs the simple-english lint.
4. Reviewer, after the verifier. One fresh `opus` agent, adversarial, four
   axes: re-derive the math, check fidelity to the anchor, check claims about
   other tools against primary sources, read as the intended reader. It
   fixes verifiable errors and lists larger suggestions without applying
   them. It ends by running `exercises/run_all.sh`.

Do not start wave 3 while a writer is still running. The verifier edits every
chapter and would collide.

## 5. Writing rules for every file

- Simple English, pragmatic register: sentences under 25 words, active
  voice, no contractions, no em-dashes, define a term at first use.
- Math in Markdown `$...$` and `$$...$$`.
- A number stated as measured must exist in a source the reader can open,
  with the same model, thread count and time step. Otherwise label it
  "estimate" or "not measured". Nobody removes those labels.
- When two chapters write the same equation, they use the same form and the
  same symbols. Put the canonical form in the verifier prompt.
- Python runs under pixi. Use `env -u PYTHONPATH pixi run python` when a
  ROS install is on the machine.

## 6. Pitfalls seen on the first run

- Writers computed `step.cpp` line numbers from a split listing with an
  offset. Several ranges were wrong. The verifier re-greps every reference.
- Two writers derived the same damping number at different time steps and
  got 0.05 and 0.12 percent. Both were right. The verifier states both with
  their conditions.
- Repo docs were stale about an external tool (a MuJoCo integrator version).
  The reviewer checks external claims against changelogs, not against the
  repo's own notes.
- One deep-dive number (906 N m/rad) did not reproduce from its stated
  inputs. The verifier read the builder code and found the real inputs.
  Label such numbers "reported" and explain the gap. Do not silently drop
  them.
- The researcher downloaded 212 MB of PDFs. Tell the user the size and
  suggest `refs/` in `.gitignore`. Do not add it yourself.
- Writers put forward references to sections that do not exist. The
  verifier checks every "see chapter NN".

- Writers paraphrased facts about other engines from the anchor repo's own
  notes. The reviewer found eight wrong statements about Newton, Isaac Lab
  and MuJoCo that way. Writers cite primary sources (docs, changelog, source
  tree) for any claim about a tool that is not the anchor.
- One exercise asked for an impossible value (a Schur complement larger than
  the matrix it came from). The reviewer re-derives every exercise, not only
  the displayed derivations.
- Scripts that only print numbers let the text drift. The verifier makes each
  script assert its numbers, so `run_all.sh` fails when text and script
  disagree.
- A chapter that cites `file:line` is pinned to one commit. Record the commit
  hash in the README so a later reader knows when references went stale.

## 7. Final report to the user

Five to ten lines. Where the folder is and how to start (README, chapter 01,
`exercises/run_all.sh`). What the reviewer changed, most serious first. Open
items the reviewer did not apply. Total size of `refs/`. Nothing else.
