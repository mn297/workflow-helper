# Proposed changes to this skill (not applied)

These came out of one session on 2026-11-15/16, in which this skill wrote three labs in `~/b2_ws/docs/lessons/`:
`rko-slam-kimera-multi.md`, then the follow-ups `rko-lio-internals.md` and `rko-slam-internals.md`. The owner will
revisit them after trying those labs. Nothing here is part of the skill until the owner approves it.
`SKILL.md` does not point to this file, so it never loads with the skill.

## Proposed (general, for every lab)

| # | Change | Where | Evidence from the session |
|---|---|---|---|
| A | **Deep-dive mode**: a follow-up lab on a tool the reader already ran. It reuses the earlier lab's `$LAB`, with new work in a subfolder, plus a prerequisites check and a catch-up block for inputs the earlier lab left to the reader. Read the source first and cite file and function for each mechanism. Stations: call the core without its wrapper (the in/out contract), follow one input through each stage with counts, the math with one term switched off or turned up, reproduce a number, profile, the output files as data. One lab per half of a tool, cross-linked. | new `deep-dive.md`, pointed to from step 1 | The skill only knew "run a tool from empty to a score"; the internals request needed all of this to be invented. |
| B | **Reproduce a number**: at least one station rebuilds a number the tool printed, from the files it wrote, with a stated tolerance. | inside A | A Python re-solve matched rko_slam's keyposes to 0.1 cm: the strongest proof of understanding in the session. |
| C | **Case file**: one real anomaly from the run, in the order it was met: what looked wrong, the guesses, the cheapest check, the number, the next prediction, the verdict, with the dead ends kept. The reader writes a guess before each reveal (a prediction, as in "Predict", not code). | lab shape, after the breaks | The owner asked for exactly this ("smell something, then look at numbers"). The height investigation was spread over five stations instead. |
| D | **Spread first**: run the baseline twice, or once with a tiny input change, and log how far the score moves. A difference smaller than that spread is no finding. | step 2, plus a rule | One dropped scan moved the odometry by 0.8 m. A single-run comparison was first written as a finding and had to be softened. |
| E | **Anomaly log**: while running, log every number that looks wrong, with the check that explained it or the guess still open. It feeds C. | step 2 | The height chain and a 0.93 m red herring (a count off by one) were the best material. |
| F | **Fix earlier labs**: when a run disproves an earlier lab, fix the text in place, link the evidence, and list the fix in the reply. | steps 6 and 8 | Three statements in Lab 1 turned out wrong. |
| G | **Cold check by script**: extract the `bash` blocks, run them in order in a fresh `$LAB`, and compare every quoted number with that output (timings excepted). Open every image the lab tells the reader to open. | step 7 | The scripted run caught two quoted outputs that no longer matched the scripts. |
| I | **Long scripts beside the lab**: a script over about 40 lines goes in `docs/lessons/<slug>/`, and the station shows only the lines that hold the mechanism. Trade-off: the lab stops being one self-contained page. Owner undecided. | rules | Lab 3 is 1085 lines, about half of it pasted scripts. |
| J | **Description**: also trigger when, after running a tool, the user asks for its internals. | frontmatter | The internals request matched the skill only through the owner naming it. |

## Rejected

- **H, the reader writes the core 5 to 10 lines**: rejected by the owner. A lab is a guided tutorial for the fastest
  internalization, not a struggle. Give every line; teach through prediction, real output and cues.

## Session-specific (keep out of the skill)

- Lab content: rko, Kimera-Multi, GLIM, the 2° IMU-vs-ground offset, the 0.8 m chaos number, the height story.
- The concrete mistakes: a ROS integer for a float parameter, a live statistics view read after a reset, a PyPI
  wheel two releases behind. At most, keep their classes as break ideas.
- Repo rules already written elsewhere: `ROS_DOMAIN_ID=99`, memory-limited scopes, pixi only (`CLAUDE.md`,
  `~/b2_ws/docs/handoff.md`).
- Using the public GitHub API when `gh` is not logged in: an environment quirk.
- A plan message before a long run: a preference the owner has not stated.
