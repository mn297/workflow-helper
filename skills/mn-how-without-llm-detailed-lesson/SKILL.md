---
name: mn-how-without-llm-detailed-lesson
description: >
  Write a guided lab: one tool on one real input (a SLAM package on a public
  dataset, a driver on a bag), run from an empty directory to a scored result.
  The agent runs it first, then writes stations the user types alone, each with
  the real output, what to notice, why, the failure signatures and the common
  confusions. Use when the user asks for a detailed lesson, a guided lab or a
  guided tour of running X with Y, or wants to internalize a workflow. Also for
  a follow-up lab on the internals of a tool the user already ran. For a short
  recipe use mn-how-without-llm. For a concept with no commands use
  mn-explaining-new-topics.
---

# Guided lab: the user drives, the answer key rides along

The user wants to internalize a workflow by driving it: they type every command, and the page beside the terminal tells them what a senior engineer would see in each output. The lab is one tool on one real input, from an empty directory to a number that scores the result. You run it first, so the lab quotes what happened, not what should happen.

Read `../mn-how-without-llm/SKILL.md` first. Its Rules apply here, except "Stay in chat": a lab is a file.

## Steps

1. **Pin the lab.** For a follow-up lab on the internals of a tool the user already ran, read `deep-dive.md` first: it changes steps 1, 2 and 7, the top of the file and the stations. Name the tool and its commit, the input (the smallest sequence that shows the behaviour), the platform, and the score that ends the lab (a trajectory error, a map, a plot). Check that the input is open to fetch: when a form, a login or a licence gates it, use a copy its owners publish openly, or stop and tell the user. Say the download size and the disk it needs before you fetch. When the input has no ground truth, pick a score the run can check by itself (a loop that ends where it began, two runs that must agree) and write its limit into the lab. Search the user's repo for earlier work on this tool (configs, specs, notes): pitfalls they already hit are the best material. Done when each of the five has a value.
2. **Run it from scratch.** Use a new directory `$LAB` and a data directory `$DATA` outside it. Keep a log: each command, its trimmed output, its wall time, and every failure you hit with the command that diagnosed it. Keep an anomaly log beside it: every number that looks wrong, with the check that explained it or the guess still open. Then measure the spread: run the baseline again, or once with one tiny input change (one scan or frame dropped), and log how far the score moves. Done when the score prints and the spread is logged.
3. **Break it on purpose.** Make two or three one-line changes that cause the mistakes people really make with this tool and input (a wrong extrinsic, a wrong topic, a wrong time unit, a wrong frame, a parameter of the wrong type). Record the signature of each: the log line, the number, the shape of the plot. Revert each one. Done when each break has a signature and the score is back.
4. **Collect the confusions.** Read the tool's issue tracker, its FAQ and the dataset's README for what people get wrong. Keep the link for each.
5. **Run the transfer task.** Run the same pipeline on a second sequence and keep the score, so the lab can give the number to hit. Where the second run needs a setting the first did not, that difference is the task: find the fix, confirm it with a rerun, and put it in the answers.
6. **Write the lab** in the shape below, to `docs/lessons/<slug>.md` in the user's repo (next to `$LAB` when there is no repo). When your runs disprove a statement in an earlier lab, fix that text in place and link the station or log line that shows it.
7. **Cold check.** Extract the lab's `bash` blocks, in order, into one script. Point `LAB` at a second empty directory that reuses `$DATA`, replace `pixi shell` with `eval "$(pixi shell-hook)"` so the script does not stop at an interactive shell, and run it. Compare every number the lab quotes with this output: only timings may differ, and a number the lab quotes as a range must fall inside it. Open every image the lab tells the reader to open. Done when every quoted number matches and the last checkpoint passes.
8. **Reply in chat:** the path, the time the lab takes, what you did not run, and each fix to an earlier lab. When the user later pastes an output that differs, diagnose it and add the case to that station's "If you see".

## Lab shape

**Top of the file**

- **Result.** What the reader has at the end, the reader's time, the download size.
- **Map.** One diagram of the whole pipeline (input, tool, outputs, score) with the station numbers on it.
- **Variables.** One `bash` block: `LAB`, `DATA`, versions. Every later block uses them. One block may open the environment's shell (`pixi shell`); say that every later block runs inside it.

**Stations.** Five to nine, in this arc: get the input, inspect the input before any run (topics, rates, frames, time base, calibration), map the input to the tool's config, run, read the output, score it. Each station has this shape, and drops a line only when it is empty:

```markdown
## 3. Inspect the bag before you run anything (4 min) — teaches: which fields the config must match

**Predict:** one question that the output answers.
**Run:** a `bash` block.
**You should see:** the real output, trimmed to the lines that matter.
**Notice:** the one to three lines an expert reads, and the healthy range of each. Answer the prediction here.
**Because:** the mechanism, in two sentences.
**If you see X instead:** the likely cause, the command that confirms it, the fix.
**Careful:** the trap at this step.
**People confuse:** the common wrong model, and the right one.
**Checkpoint:** one command and the exact line that proves the station passed.
```

**After the stations**, in this order. Each section hands the reader more of the work.

- **Break it on purpose.** Each break from step 3: the one-line change, the signature, why it happens, the revert.
- **Case file.** One real anomaly from the anomaly log, told in the order you met it: what looked wrong, the guesses, the cheapest check, its number, the next prediction, the verdict. Keep the dead ends: they show which checks are cheap. Before each reveal, the reader writes down a guess, as on a **Predict** line. Pick the anomaly that took the most checks to explain, and tell its whole story here: a station that meets it links to this section. Leave the section out when the anomaly log is empty.
- **Now without the guide.** The transfer task: the second sequence, a checklist of five to seven lines with no commands, and the score to hit. Its answer goes at the bottom of the file.
- **Recall.** Five questions to answer from memory. Answers at the bottom of the file.
- **Find it yourself next time.** The discovery commands and the pages you opened.
- **Tested.** The machine, what you ran, what you did not run.

## Rules

- **Driver seat.** A command comes within the first three lines of every station. Theory comes after the output it explains.
- **On the screen.** Every sentence points at something the reader can see: a line of output, a config key, a curve in a plot. Cut the sentences that point at nothing.
- **Real output.** Quote only what you ran. Mark anything else "untested", and say whether it comes from the docs or from your guess.
- **Cues.** "Notice" names the lines and the numbers that separate healthy from broken. That is what the reader came for.
- **Every line given.** The lab gives every line of code. The reader's work is the prediction, the run and the reading of the output.
- **Spread.** A difference between two runs is a finding only when it is larger than the spread from step 2. Quote the spread beside it. Quote a number that moves between reruns of the same input as a range.
- **Scripts beside the lab.** A script long enough to bury its station's story (about 40 lines or more) goes in `docs/lessons/<slug>/`, and the Variables block names that folder. The station runs it from there and shows only the lines that hold the mechanism. A shorter script stays inline as a heredoc.
- **Skippable.** Each heading says what the station teaches, so a reader who knows it jumps to the checkpoint.
- **One sitting.** The reader's time is 60 minutes or less, downloads excluded. Split a longer lab into two and say where.
- **Diagrams for shape.** Draw one (Mermaid) where the content is a shape: a frame tree, a data flow, a timeline. Text carries the rest.
