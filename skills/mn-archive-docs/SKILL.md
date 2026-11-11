---
name: mn-archive-docs
description: >
  Move old docs out of search results without losing them. The user names a
  folder or files (specs, plans, handoffs, state logs, dated reports); the
  skill decides which ones are finished or superseded, moves them to an
  archive/ subfolder with git mv, hides that folder from ripgrep with a
  .ignore file, and fixes the paths that point to the moved files. Use when
  the user says "archive old docs", "old specs pollute rg", "clean up the
  specs folder", "hide finished specs from search", "too many stale md
  files", or asks which docs in a folder are still live. Not for deleting
  docs and not for a new docs layout (mn-organizing-project-docs).
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docs, Specs, Archive, ripgrep, Search"
  category: "organization"
---

# mn-archive-docs

Old docs stay in git but leave the search results. Each finished doc moves to `<folder>/archive/`. A `.ignore` file (ripgrep's own ignore file; git does not read it) hides that folder from `rg` and from every agent tool built on it.

The target is the folder or the files that the user names. With no target, list the folders that hold many dated `.md` files and ask which one.

## Steps

1. **List the docs.** One doc is a main file plus its sidecars: the files with the same stem, such as `<stem>.state.md` or `<stem>-research.txt`. A doc moves or stays as one unit.
2. **Collect evidence for each doc.** Do not judge from the file name or the date alone.
   - `git status --short <folder>`: uncommitted or untracked files.
   - `git log -1 --format='%ad %s' --date=short -- <file>`: the last change.
   - The status lines inside the doc and its state file: `rg -n -i 'next step|status|step [0-9]+: |superseded|replaced by' <file>`.
   - Who points to it: `rg -l '<stem>' .`
3. **Give each doc one verdict.**

   | Verdict | Evidence | Action |
   |---|---|---|
   | finished | Every step that an agent can run is done. Open checks that only the owner can run do not keep it live. | archive |
   | superseded | A newer doc or revision says that it replaces this one. | archive |
   | live | Uncommitted or untracked. Or work is not started, or a builder step is next. Or it describes how the current code works (a README, a runbook, a reference page), at any age. | keep |
   | unclear | The evidence conflicts or is missing. | keep, and ask |

4. **Move.** `mkdir -p <folder>/archive`, then `git mv` each archived doc with its sidecars. In a folder that git does not track, use `mv` and tell the user that no history protects the move.
5. **Hide.** Write `<folder>/.ignore` with the one line `archive/`. Keep the file next to the docs. A root `.ignore` with the full path `docs/specs/archive/` leaks when `rg` gets two search paths (measured, ripgrep 15.1.0).
6. **Fix the paths** (commands below). Three kinds of reference break:
   - a full path, anywhere in the repo: `<folder>/<name>` becomes `<folder>/archive/<name>`;
   - a bare file name in a live doc that points to an archived doc: add `archive/`;
   - a bare file name in an archived doc that points to a live doc: add `../`.
   A bare name between two archived docs stays correct.
7. **Leave a note for agents.** Add the block below to the project's `CLAUDE.md` or `AGENTS.md`. If the project has neither, create `CLAUDE.md` with it.
8. **Check** (commands below), then report. Do not commit unless the user asks.

## Commands

Give `rg` a path in every scripted call. Without one, in a shell with no terminal, it can read stdin and hang (seen once; the path fixed it).

```bash
DIR=docs/specs                       # the target folder
STEMS='2026-11-05-foo|2026-11-06-bar'   # stems of the moved docs, joined with |

# Step 6, full paths: rewrite everywhere in the repo. The archive is hidden now, so name it too.
rg -l "$DIR/($STEMS)" . "$DIR/archive/" | xargs -r perl -pi -e "s{\Q$DIR\E/(?=(?:$STEMS))}{$DIR/archive/}g"

# Step 6, bare names: list them, then edit each line by hand.
rg -n -P "(?<![\w/-])($STEMS)" "$DIR"            # live docs: add archive/
rg -n -P "(?<![\w/-])20\d\d-" "$DIR/archive/"    # archived docs: add ../ where the target is live

# Step 8: every line must print the expected count.
rg -n -P "(?<!archive/)($STEMS)" . | wc -l       # 0: no stale path outside the archive
rg -n "$DIR/($STEMS)" "$DIR/archive/" | wc -l    # 0: no stale full path inside the archive
rg --files "$DIR" | rg -c '/archive/'            # no output: the archive is hidden
rg --files "$DIR" . | rg -c '/archive/'          # no output: still hidden with two search paths
rg --files "$DIR/archive/" | wc -l               # the number of moved files: an explicit path still works
```

Change the `20\d\d-` pattern when the doc names do not start with a date.

## Note for agents

```markdown
Docs in progress live in `<folder>/`. Finished docs and their state files live in
`<folder>/archive/`. `<folder>/.ignore` hides that folder from ripgrep. To search it, pass the
path: `rg <pattern> <folder>/archive/`.

To archive a doc, `git mv` it and its sidecar files there, then fix the paths that point to it.
```

## Report

Answer first: how many docs moved and how many stayed. Then one table: doc, verdict, the evidence in a few words. For each finished doc with open owner checks, name the checks. End with the undo command: `git mv <folder>/archive/<stem>* <folder>/`.

## Limits

- The `.ignore` file hides the folder from ripgrep. Other search tools (an IDE index, a code graph, a glob tool) may still list the archive. Untested.
- The skill moves docs. It never deletes one.
