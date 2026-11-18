# Deep-dive: a follow-up lab on a tool's internals

A deep-dive opens the tool the reader already ran, one mechanism per station, on the run they already have. It starts from the earlier lab's results, not from an empty directory. Everything in `SKILL.md` applies, except where this file says otherwise.

## What changes in the steps

- **Step 1, pin.** Pin the earlier lab instead of a new input: its file, its `$LAB`, the tool's commit. Pick one half of the tool (the odometry core, the SLAM back end): one lab per half, each linking to the other and to the earlier lab. Read the source before any run. For each mechanism a station will show, note the file and the function that hold it. Done when every planned station has its citation.
- **Step 2, run.** Reuse the earlier lab's `$LAB` and write new work to a subfolder (`$LAB/internals`), so the earlier lab's results stay as its text quotes them. List each output of the earlier lab that this one reads, and each input the earlier lab left to the reader (its transfer task, say).
- **Step 7, cold check.** Start from a cold copy of the earlier lab (its own cold-check directory works), then run this lab's blocks in a fresh subfolder.

## Top of the file

- **Before you start**, in the Result block: the earlier lab, done in `$LAB`, with a link. Name the other half's lab and say whether this one needs it.
- **Catch-up**, after the lab shell: one block for each input the earlier lab left to the reader. Head it with the command whose output says the reader can skip it, the time it takes and the disk it writes.

## Stations

Build the stations from these kinds, in the order the data flows through the tool. Every deep-dive has a "reproduce a number" station; the other kinds fit most tools.

- **Call the core without its wrapper.** Drive the library under the node by hand on the same input. Teaches the in/out contract of each call. The checkpoint: the by-hand result matches the node's to a stated tolerance.
- **Follow one input through each stage.** One scan, one frame or one message, with its count after each stage (in range, downsampled, matched).
- **Switch one term off, then turn it up.** Rerun with one cost term at zero and at ten times its default. The outputs show what the term buys.
- **Reproduce a number.** Rebuild a number the tool printed from the files it wrote, and state the tolerance in the checkpoint. This is the strongest proof of understanding a lab can give.
- **Profile.** Read the tool's profiler, or time each stage. Say what share of the run each stage takes.
- **Read the output files as data.** Open each file the tool wrote, name its fields, and load it with a short script in the lesson folder.

Each **Because** line cites the file and the function, at the pinned commit, that hold the mechanism it explains.
