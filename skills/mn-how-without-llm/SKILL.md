---
name: mn-how-without-llm
description: >
  Answer a "how do I do X" request with a self-contained manual recipe: the raw
  commands a person types without an LLM, in order, each with its check, plus
  the files to edit by hand, gotchas, variations, undo, and where to look it up
  next time. Use when the user asks how to do, set up, install, configure, build
  or run something, or asks for "raw commands", "by hand", "without LLM", or
  "how one would do it". For how a concept or system works, use
  mn-explaining-new-topics.
---

# How to do it without an LLM

The user wants a recipe they can run alone, today and next month, with no agent in the loop. The answer is the recipe, not a change to their repo. Write it so a reader who has only this reply and a terminal finishes the task.

## Steps

1. **Pin the target.** Name the tool, the version and the platform. Read the repo for a convention that already exists (a `pixi.toml`, a `Makefile`, a README command) and follow it. When a choice is open (distro, version, flavour), pick a default, put it in a shell variable at the top (`D=jazzy`), and list the other values in a comment. Ask only when no default is sensible.
2. **Ground every command.** Check each one against the real tool: `--help`, `man`, current docs (context7 or the tool's site), or a dry run in the scratchpad (`--dry-run`, `--no-install`, `pixi search`). Done when each command is either run or marked untested.
3. **Write the reply** in the shape below.
4. **Clean up** anything the dry run left in the scratchpad.

## Reply shape

Use these sections in this order. Drop a section only when it is empty for this task.

1. **Result first.** One or two sentences: what the reader ends up with, and which tool does it and why.
2. **Before you start.** What must exist already, each with a command that checks it (`pixi --version`).
3. **Commands.** One fenced `bash` block that runs top to bottom when pasted. Variables at the top. A numbered comment heads each step and says what it does. Put the expected result or a check after each step that can fail. Every command is raw: the stock CLI, not a repo task or alias. When the repo has a shortcut for the same thing, name it in one line after the block.
4. **Edit by hand.** Config the CLI cannot write. Give the file path and the exact snippet.
5. **Gotchas.** The places people trip, and the reason behind each step that looks odd. One line each.
6. **Variations.** Other versions, platforms or options, one line each, with the command that changes.
7. **Check it works.** One end-to-end test and what success prints.
8. **Undo.** How to remove what the recipe made.
9. **Find it yourself next time.** The discovery commands (`pixi search`, `apt-cache policy`, `<tool> <sub> --help`) and the doc pages, with links you have opened, so the reader can solve the next case alone.
10. **Tested.** One line: what you ran, what you did not run, and the risk left.

## Rules

- **Copy-paste safe.** Every placeholder is a variable set at the top. There are no `<your-thing>` gaps inside commands and no prompts that block a paste.
- **The user's stack.** Python environments use pixi (`pixi init`, `pixi add`, `pixi add --pypi`), never conda or a bare `pip install`. ROS comes from RoboStack channels (`robostack-<distro>`, then `conda-forge`).
- **Flag danger before the command.** Mark `sudo`, deletes, overwrites, and anything that moves hardware with a warning line above the command, never inside it.
- **Name the source of each fact.** Separate what you ran from what docs say and from your guess, and keep "may" and "untested" where they hold.
- **Stay in chat.** Write no file unless the user asks to save the recipe.
