# Pitfalls from earlier runs

Each item is a failure that happened, and the rule it produced. Most rules
already sit in `SKILL.md` or in `agent-prompts.md`. This file keeps the reason
behind each one, so a rule is not dropped as unexplained.

## Run 1 (an engine comparison primer)

- Writers computed line numbers of an anchor source file from a split
  listing with an offset. Several ranges were wrong. The verifier re-greps
  every reference.
- Two writers derived the same damping number at two time steps and got two
  values. Both were right. The verifier states both with their conditions.
- Repo docs were stale about an external tool (the integrator version of
  another engine). The reviewer checks external claims against changelogs,
  not against the repo's own notes.
- One reported number in the anchor's docs did not reproduce from its stated
  inputs. The verifier read the builder code and found the real inputs.
  Label such numbers "reported" and explain the gap. Do not silently drop
  them.
- The researcher can download hundreds of MB of PDFs. Tell the user the size
  and suggest `refs/` in `.gitignore`. Do not add it yourself.
- Writers put forward references to sections that do not exist. The
  verifier checks every "see chapter NN".
- Writers paraphrased facts about other engines from the anchor repo's own
  notes. The reviewer found several wrong statements about other engines
  that way. Writers cite primary sources (docs, changelog, source tree) for
  any claim about a tool that is not the anchor.
- One exercise asked for an impossible value (a Schur complement larger than
  the matrix it came from). The reviewer re-derives every exercise, not only
  the displayed derivations.
- Scripts that only print numbers let the text drift. The verifier makes each
  script assert its numbers, so `run_all.sh` fails when text and script
  disagree.
- A chapter that cites `file:line` is pinned to one commit. Record the commit
  hash in the README so a later reader knows when references went stale.

## Run 2 (a Lie-groups primer)

- The orchestrator read the anchor with one `cat -n` over several files.
  Every file after the first had offset line numbers. Never pass line numbers
  to writers. Tell them to grep.
- Several writers found the same anchor bug on their own, and no test
  covered it. Reproduce such a claim once, relay it, and give it the first
  line of the final report.
- The orchestrator built a pixi environment while the workspace already had
  uv. The user wanted one environment per workspace. The primer then needed
  a rewrite of every run command.
- A per-primer environment did not have the anchor installed. The verifier
  added `sys.path.insert(0, "<absolute path>")` to several scripts. Install
  the anchor editable in wave 0 instead.
- The user-site `~/.local` numpy leaked into the new environment and showed a
  wrong version. Check `numpy.__file__` once after setup.
- Writers removed spaces from display math to quiet the lint, and the
  verifier had to restore them.
- The arXiv tool returned HTTP 429 after one call. The researcher opened the
  arXiv abstract pages directly. Some publishers block plain fetches.
- Readers want online courses. The researcher prompt asks for a "Courses and
  videos" section in every run.
- The visualizer's Play button stalled on sliders with a fine step: rounding
  each frame's small increment back to the step undid it. Keep a float
  accumulator and snap only what is shown.
- A range input snaps its value to the step, so the label showed 1.5700 while
  the maths used 1.5708. Print the value the maths uses.

## Run 3: interactive lessons

- Cell markers (`# %%`, to step through a script in the editor) came after a
  primer was done. That meant converting every script. The verifier now
  builds the cells from the start (`references/interactive-exercises.md`).
- Scripts that only run top to bottom hid rerun bugs: a filter cell that
  updates `x` and `P` in place, a random generator made in an earlier cell.
  `run_cells.py` runs each cell twice and compares the printed text.
- A kernel started in the workspace root found a submodule folder with the
  name of an installed package (for example `./drake/`), and the import
  failed with `ImportError: initialization failed`. The kernel must start in
  the folder of the script, which is the VS Code default.
- A chapter cited line numbers inside a `code-notebook/` script. The
  conversion moved every line. After any change to a script, grep the
  chapters for citations into `code-notebook/`.
- The assert counter matched `check_numbers()` as a check and missed the
  exact-text helper `printed(`. Count the real helpers of the primer.
- Old scripts stated some exercise answers only in a docstring, and one
  docstring claimed an assert that did not exist. A converted exercise cell
  asserts the answer, or it points at the step that does.

## Run 4: simple copies

- Cell lessons are hard to read as a whole: check cells and notes cut the
  logic into small pieces. `build_simple.py` now writes a plain copy of each
  lesson with one comment banner per step
  (`references/interactive-exercises.md`, section "Simple copies").
- Some lessons failed as plain copies at first. A check cell computed a value
  that a later step used. The script now keeps such a statement. Its
  `--check` runs each lesson and its copy and compares the printed lines.
- A measurement script printed `ms_per_step` as a bare number. Two runs
  print other times, so the simple-copy test failed. Times now carry the unit
  `ms` or `s`, and both tests ignore them.
- The lessons of one primer set a stdout tee in the setup cell for their text
  checks. Each simple copy then began with a long block of tee code. Code
  that only the checks use now goes into a check cell.
- Two sibling folders read better than a nested pair such as `exercises/`
  and `exercises/clean/`: `code-notebook/` for the cell lessons and
  `code-simple/` for the copies.
