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
  "teach me X from basics", "from scratch, each concept", "deep research good
  resources and collect them to a folder", or "what did we do versus engine
  Y". Make sure to use this skill
  even when the user names no folder and no chapter list. Propose both.
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

Reference instances. Read one `README.md` and one chapter before the first
run on a new topic, to see the shape.

- `/home/john/tree_physics/tutorial/`: tree-sim versus Newton, MuJoCo, Isaac
  Lab, built 2026-10-02, before the folder naming rule in section 1.
- `/home/john/practice_kinematics/tutorial-lie-algebra/`: Lie groups and manifolds,
  anchored on `featherstone_playground`, with library clones in `upstream/`,
  a Notation section in the README, and the visualizer
  `viz/lie-instruments.html`, built 2026-10-03.

## Me

Robotics and simulation engineer. I build things with help, then want to
understand the mathematics under them. Strong at code, weak at the derivation
chain. Assume vectors, matrices, derivatives, Python. Build everything else.

## 1. Pin down six inputs, then move

Take these from the conversation. Propose any that are missing and proceed.
Ask at most one question, and only when two readings lead to different
folders.

| Input | Default when missing |
|---|---|
| Topic | The thing the user named |
| Anchor | A repo path the user owns that uses the topic. If none, one target problem solved in the simplest library for that topic, then mapped to the library the user wants to learn (example: FEM anchor = a cantilever in scikit-fem, then the same problem in FEniCSx) |
| Reader background | The "Me" section above |
| Folder | `<repo>/tutorial-<topic-slug>/` if the anchor is a repo, else `~/tutorials/tutorial-<topic-slug>/`. The slug is one to three lowercase words in kebab case that name the topic, not the anchor: `tutorial-lie-algebra`, `tutorial-fem`, `tutorial-factor-graphs`. Never a bare `tutorial/`, because a repo can hold several primers. If the folder exists, add a word (`tutorial-lie-algebra-se3`), never overwrite |
| Ladder | Propose 8 to 12 chapters, one concept each. Chapter 1 is the mathematical object the reader cannot skip. The last chapter is "what we did versus the alternatives" |
| Environment | The Python environment the workspace already has (uv or pixi). Add the primer's packages there and install the anchor in editable mode. When the workspace has none, create one with pixi. Never add a second one |

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
  exercises/              exNN_<slug>.py per chapter snippet, README.md, run_all.sh, out/ for generated GIFs
  upstream/               shallow clones of libraries the anchor does not contain, gitignored, hashes in README
  viz/<name>.html         the course visualizer: one interactive instrument per chapter, also published as an Artifact
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

Run it in six waves, 0 to 5. The prompts are in `references/agent-prompts.md`.
Fill the placeholders and send them as written. They encode the lessons of
the earlier runs. Before wave 0 on a new topic, read `references/pitfalls.md`:
each failure from earlier runs and the rule it produced.

0. Ground the sources yourself, before any agent starts.
   - Environment: find the workspace environment, add the packages, install
     the anchor editable. Run the anchor test suite in it and record the
     result as the first measured fact. If a memory says which interpreter
     works, test it again. Shell state goes stale (ROS paths, `~/.local`
     site-packages).
   - Libraries: shallow-clone every library the user wants to learn that the
     workspace does not contain into `<folder>/upstream/`. Record each commit
     hash. The writers then cite `file:line` from primary source, not memory.
     Note when the installed version differs from the clone.
   - Completion: the anchor test result is recorded, `numpy.__file__` points
     inside the workspace environment, and every clone has its hash.
1. Write `README.md` yourself, with the final chapter table, the pinned
   sources table and a Notation section. Notation holds the canonical
   equations and symbols, and the "anchor bridge": which anchor function is
   which object of the topic. Writers, verifier and reviewer read them there.
   Completion: `README.md` holds all three, with every hash from wave 0.
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
   - Completion: every writer sent its report, and every chapter file in the
     README table exists. The researcher can still run.
3. Verifier, after all writers report. One fresh agent with
   `model: "opus"` because it writes scripts (forks ignore the model
   override). It extracts snippets to `exercises/`, runs them, fixes text or
   script where they disagree, reconciles the cross-chapter items you list
   from the writers' reports, re-greps every `file:line`, builds the
   glossary, updates `README.md`, and runs the simple-english lint.
   Completion: `run_all.sh` exits 0, its failure exit is tested, and the
   report lists every text fix.
4. Reviewer, after the verifier and the researcher. One fresh `opus` agent,
   adversarial, four axes: re-derive the math, check fidelity to the anchor,
   check claims about other tools against primary sources, read as the
   intended reader. It fixes verifiable errors and lists larger suggestions
   without applying them. Completion: `exercises/run_all.sh` exits 0 after
   its last fix.
5. Visualizer, after the reviewer, by you. One interactive page with one
   instrument per chapter, whose default settings reproduce the chapter's
   worked numbers. Follow `references/visualizer.md`. Render the page only
   in the isolated CPU-rendering headless Chrome that file names, never in
   the user's own Chrome. Completion: the node check passes for every number
   the chapter scripts assert, the page is published, a copy sits in
   `viz/`, and `README.md` names both.

Do not start wave 3 while a writer is still running. The verifier edits every
chapter, so the two collide. The researcher touches only `resources.md` and
`refs/`, so the verifier can start while it runs.

During waves 2 to 4, two events need a message, not an edit:

- A writer reports a bug in the anchor. Reproduce it yourself against a
  reference implementation. Then send the confirmed facts with `SendMessage`
  to every writer still running whose chapters touch it. One chapter holds
  the full account and the others refer to it. Nobody edits the anchor.
  Report the bug to the user in the next reply.
- The user changes a requirement (another environment, a path rule). Send it
  to the agent that owns the files. Edit a file yourself only when no running
  agent owns it.

## 5. Writing rules for every file

- Simple English, pragmatic register: sentences under 25 words, active
  voice, no contractions, no em-dashes, define a term at first use.
- Math in Markdown `$...$` and `$$...$$`.
- A number stated as measured must exist in a source the reader can open,
  with the same model, thread count and time step. Otherwise label it
  "estimate" or "not measured". Nobody removes those labels.
- When two chapters write the same equation, they use the same form and the
  same symbols. The canonical form lives in the README Notation section.
- Python runs in the workspace environment (input "Environment"). A shell
  that sourced ROS puts its own packages on `PYTHONPATH` and
  `LD_LIBRARY_PATH`. If the session inherited them, prefix your own commands
  with `env -u PYTHONPATH -u LD_LIBRARY_PATH`. The primer shows the plain
  command.
- Every `file:line` path in the primer starts at the primer folder:
  `../<dir>/...` for a workspace file, `upstream/<lib>/...` for a clone.
  A section can name its base once ("All references are to
  `../<dir>/`") and then write shorter paths below it. Verifiers keep that
  form. Shell commands run from the workspace root, so their paths start there.
  Scripts hold no absolute paths and import the anchor by its installed
  package name. Copy a small test helper into the script that needs it.
- The simple-english lint counts math and table rows as prose. Those hits
  are false positives. Leave math spacing as written.

## 6. Final report to the user

Five to ten lines. Any bug found in the anchor, first. Where the folder is
and how to go through it: per chapter, read, redo the derivation on paper,
run its script, open the `file:line`, do the exercises. The visualizer link.
What the reviewer changed, most serious first. Open items the reviewer did
not apply. Total size of `refs/`. Nothing else.
