# Pitfalls from earlier runs

Each item is a failure that happened, and the rule it produced. Most rules
already sit in `SKILL.md` or in `agent-prompts.md`. This file keeps the reason
behind each one, so a rule is not dropped as unexplained.

## First run (tree physics, 2026-10-02)

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

## Second run (Lie groups, 2026-10-03)

- The orchestrator read the anchor with one `cat -n` over several files.
  Every file after the first had offset line numbers. Never pass line numbers
  to writers. Tell them to grep.
- Four of six writers found the same anchor bug on their own (forward
  kinematics composed inverse poses, and no test covered it). Reproduce such
  a claim once, relay it, and give it the first line of the final report.
- The orchestrator built a pixi environment while the workspace already had
  uv. The user said "clean up env in this ws, just one uv". The primer
  then needed a rewrite of every run command.
- A per-primer environment did not have the anchor installed. The verifier
  added `sys.path.insert(0, "/home/john/...")` to eight scripts, and the user
  objected. Install the anchor editable in wave 0.
- The user-site `~/.local` numpy leaked into the new environment and showed a
  wrong version. Check `numpy.__file__` once after setup.
- Writers removed spaces from display math to quiet the lint, and the
  verifier had to restore them.
- The arXiv tool returned HTTP 429 after one call. The researcher opened the
  arXiv abstract pages directly. Some publishers block plain fetches.
- The user asked for online courses. The researcher prompt now asks for a
  "Courses and videos" section in every run.
- The visualizer's Play button stalled on sliders with a fine step: rounding
  each frame's small increment back to the step undid it. Keep a float
  accumulator and snap only what is shown.
- A range input snaps its value to the step, so the label showed 1.5700 while
  the maths used 1.5708. Print the value the maths uses.
