---
name: mn-archive-docs
description: >
  Move old docs out of search results without losing them. The user names a
  folder or files (specs, plans, handoffs, prompts, changelogs, code traces,
  state logs, dated reports, topic subfolders); the skill decides which ones are
  finished, superseded or filed in the wrong folder, moves them with git mv to
  an archive/ subfolder or to the folder they belong in, hides the archive from
  ripgrep with a .ignore file, and fixes every path that points to a moved file.
  Use when the user says "archive old docs", "old specs pollute rg", "clean up
  the plans folder", "lotta trash in docs", "hide finished specs from search",
  "too many stale md files", "is rg clean now", or asks which docs in a folder
  are still live. Not for deleting docs and not for a new docs layout
  (mn-organizing-project-docs).
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docs, Specs, Archive, ripgrep, Search"
  category: "organization"
---

# mn-archive-docs

Old docs stay in git but leave the search results. Each finished doc moves to `<folder>/archive/`. A `.ignore` file (ripgrep's own ignore file; git does not read it) hides that folder from `rg` and from every agent tool built on it. An explicit path still searches it.

The target is the folder or the files that the user names. With no target, list the folders that hold many dated `.md` files and ask which one.

## Steps

1. **List the units.** One unit moves or stays as a whole:
   - a doc: the main file plus its sidecars, the files with the same stem (`<stem>.state.md`, `<stem>-research.txt`);
   - a topic subfolder (`plans/vbd-port/`): every file in it, scripts and results included.
   Run `git status --short` on the whole repo now and keep the output. A modified file that you did not touch belongs to someone else (another session may work in the same checkout).
2. **Collect evidence for each unit.** Do not judge from the name or the date alone. Run the checks as one loop over all units (see Commands).
   - `git status --short <unit>`: uncommitted or untracked.
   - `git log -1 --format='%ad %s' --date=short -- <unit>`: the last change. A recent commit that only fixed paths says nothing.
   - Status lines: `rg -n -i 'next step|status|step [0-9]+: |superseded|replaced by|not started|paused' <unit>`.
   - Progress: the count of `- [x]` against `- [ ]`, and the state column of any wave or task table.
   - The docs it names: for each `docs/...md` path in it, is the target live, already archived, or missing? A prompt or handoff whose spec is archived is finished.
   - The code it names: how many of the file paths in it still exist. A doc about code that is mostly gone no longer describes the current code.
   - Later history: `git log --oneline -i --grep='<topic word>'`. A later commit that merged the work, dropped the commands, or replaced the design settles the verdict.
   - Who cites it: `rg -l '<stem>' .`. A live README or source comment that cites the doc as its explanation keeps it live.
3. **Give each unit one verdict.**

   | Verdict | Evidence | Action |
   |---|---|---|
   | finished | Every step that an agent can run is done. Open checks that only the owner can run do not keep it live. | archive |
   | superseded | A newer doc, revision or commit replaces it. | archive |
   | misfiled | It is still useful but belongs to another folder of the project, such as a research note in `reference/` when the project has `research/`. | move it there |
   | live | Uncommitted or untracked. Or work is not started, or a builder step is next. Or it describes how the current code works (most paths it names exist), at any age. Or live code cites it as its explanation. | keep |
   | unclear | The evidence conflicts or is missing. | keep, and ask |

   When nobody can answer (an unattended run), keep every unclear unit and list it in the report.
4. **Move.** `mkdir -p <folder>/archive`, then `git mv` each archived unit: a doc with its sidecars, or a topic subfolder whole. Move a misfiled doc with `git mv` to its folder and add a row to that folder's index if it has one. In a folder that git does not track, use `mv` and tell the user that no history protects the move.
5. **Hide.** Write `<folder>/.ignore` with the one line `/archive/`. Keep the file next to the docs.
   - Anchor the pattern with the leading `/`. A bare `archive/` matches every folder named `archive` below, so a topic that already had its own `archive/` (`plans/factor-graphs/archive/`) stays hidden even under the explicit path `<folder>/archive/` (measured, ripgrep 14.1.1).
   - Name the folder in the pattern. A `*` pattern also hides the files under an explicit path, so `rg x <folder>/archive/` finds nothing (measured, ripgrep 14.1.1).
   - A root `.ignore` with the full path `docs/specs/archive/` leaks when `rg` gets two search paths (measured, ripgrep 15.1.0).
   - Run `git check-ignore -v <folder>/.ignore`. If a parent `.gitignore` rule matches it, the file is never committed: add `!<folder>/.ignore` after that rule.
6. **Fix the paths** (commands below). Five kinds of reference break:
   - a path that names the moved unit through its folder, anywhere in the repo, in any form: `docs/plans/<name>`, `../plans/<name>`, `plans/<name>`. Insert `archive/` after the folder name;
   - a bare file name in a live doc that points to an archived doc: add `archive/`;
   - a bare file name in an archived doc that points to a live doc: add `../`;
   - a `../` link inside a moved doc: the doc now sits one level deeper. If the target resolved before the move, add one `../`. If it was already broken, leave it and name it in the report;
   - a row that describes the folder in a docs index (`docs/README.md`): say what stays in the folder and that `archive/` holds the finished docs. Read the index's conventions too: a rule such as "delete a finished doc unless something cites it" now conflicts with the archive, so point it at the archive or ask the user.
   A bare name between two archived docs stays correct, and so does a link between two units that moved together.
7. **Leave a note for agents.** Add the block below to the project's `CLAUDE.md` or `AGENTS.md`. If the file already has the note for another folder, add this folder to it. If the project has neither file, create `CLAUDE.md` with it.
8. **Check** (commands below). If the project has its own docs link checker, run it too, and compare its misses with a run before your change. Then report.
9. **Commit only when the user asks.** See "Commit in a shared checkout".

## Commands

Give `rg` a path in every scripted call. Without one, in a shell with no terminal, it can read stdin and hang. File names can hold spaces, so pass file lists with `-0` and `xargs -0`. In some agent shells `rg` is a shell function, not a program: a script file or `sh -c` then fails with `rg: command not found`. Run the commands in the agent's own shell, or check `type rg` and call the binary it names.

Search with `--no-ignore-dot` wherever a stale path can hide. By the time you rewrite, earlier archives are hidden (`docs/specs/archive/`, or the first folder's new archive when one run archives two folders), and their docs still cite the units you just moved.

```bash
DIR=docs/plans                    # the target folder
BASE=$(basename "$DIR")           # matches docs/plans/x, ../plans/x and plans/x alike
UNITS=($(cd "$DIR" && ls -d */ *.md | sed 's|/$||' | grep -vx archive))   # every unit, before the move
B='(?![\w-])'                     # end of a stem: keeps `foo` from matching `foo-spec`

# Step 2: the docs that each unit names, and whether each target is live, archived or missing.
for u in "${UNITS[@]}"; do echo "== $u"; rg -o --no-filename 'docs/[\w./-]+\.md' "$DIR/$u" | sort -u |
  while read -r p; do a="$(dirname "$p")/archive/$(basename "$p")"
    if [ -e "$p" ]; then case "$p" in */archive/*) echo "  archived $p";; *) echo "  live $p";; esac
    elif [ -e "$a" ]; then echo "  archived $p"; else echo "  missing $p"; fi; done; done

# Step 6: the units you moved (doc files and topic folders), as one regex.
MOVED=(2026-08-01-foo.md vbd-port 2026-08-09-bar.v2.md)
STEMS=$(printf '%s\n' "${MOVED[@]}" | sed 's/\.md$//; s/[.]/\\./g' | paste -sd'|')

# Step 6, paths: rewrite everywhere in the repo, hidden archives included.
rg -l -0 --no-ignore-dot -P "(?<![\w-])$BASE/(?:$STEMS)$B" . |
  xargs -0 -r perl -pi -e "s{(?<![\w-])\Q$BASE\E/(?=(?:$STEMS)$B)}{$BASE/archive/}g"

# Step 6, bare names: list them, then edit each line by hand.
rg -n -P "(?<![\w/-])(?:$STEMS)$B" "$DIR"        # live docs: add archive/
rg -n -P "(?<![\w/-])20\d\d-" "$DIR/archive/"    # archived docs: add ../ where the target is live

# Step 6, ../ links inside the moved docs.
rg -n -o -P '(?:\]\(|`)\K\.\./[^)`#\s]+' "$DIR/archive/" | while IFS=: read -r f n link; do
  d=$(dirname "$f"); [ -e "$d/$link" ] && continue
  if [ -e "$d/../$link" ]; then echo "add ../  $f:$n $link"; else echo "broken before the move  $f:$n $link"; fi; done

# Step 8: every line must print the expected value.
rg -n --no-ignore-dot -P "(?<![\w-])$BASE/(?:$STEMS)$B" . | wc -l   # 0: no stale path anywhere, hidden archives included
rg --files "$DIR" | rg -c "^$DIR/archive/"     # no output: the archive is hidden
rg --files "$DIR" . | rg -c "$DIR/archive/"    # no output: still hidden with two search paths
diff <(rg --files "$DIR/archive/" | sort) <(rg --files --no-ignore-dot "$DIR/archive/" | sort)   # no output: an explicit path finds every file
```

- Change the `20\d\d-` pattern when the doc names do not start with a date.
- In the two-path check, match this archive only. A bare `/archive/` also counts every other archive in the repo.
- For a misfiled doc, run the same rewrite with the old and new folder: replace `$BASE/` with the new path, such as `research/uncategorized/`.
- Read the diff of each code file that the rewrite touched. The path should sit in a string, comment or docstring.

## Commit in a shared checkout

Another session may edit files in the same checkout while you work. Commit your work alone, and give other work its own commits when the user asks for everything.

1. Sort the modified files. A file is yours if undoing your path inserts gives back its old lines:

   ```bash
   git diff --name-only -z | while IFS= read -r -d '' f; do
     [ -d "$f" ] && { echo "check  $f (submodule)"; continue; }
     d=$(git diff -U0 -- "$f" | rg -a -v '^(--- |\+\+\+ |@@|diff |index )')
     old=$(printf '%s\n' "$d" | rg -a '^-' | cut -c2- | md5sum)
     new=$(printf '%s\n' "$d" | rg -a '^\+' | cut -c2- | perl -pe "s{\Q$BASE\E/archive/}{$BASE/}g" | md5sum)
     [ "$old" = "$new" ] && echo "yours  $f" || echo "check  $f"; done
   ```

   Read the diff of each `check` file. The files you edited by hand (the agent note, an index row) land there too.
2. When one file holds your lines and someone else's, stage your version only: write the file without their lines to a temporary file, then `git update-index --cacheinfo 100644,$(git hash-object -w <tmp>),<file>`.
3. Never commit raw data, environments or caches (a capture folder at the repo root, `.pixi/`, `out/`). Tell the user where they belong.

## Optional: is rg clean?

When the user asks how clean search is, measure it before you suggest more:

```bash
rg --files . | awk -F/ '{print $2}' | sort | uniq -c | sort -rn | head   # what rg sees, by top folder
rg --files . | rg -o '^.*?/archive/' | sort | uniq -c                    # archive folders still visible
```

- An old `archive/` folder with no `.ignore`: add one next to it.
- A vendored checkout that git tracks (`third_party/IsaacLab/`): write `third_party/.ignore` with `/IsaacLab/`, and add to the agent note how to search it by path (`rg <name> third_party/IsaacLab/source`). A repo-wide search then shows the project's own use of an API first, and the upstream source stays one explicit path away.
- An untracked data dump or a leftover folder: report it. Before you delete a leftover, check that it holds no source (only caches or an environment), that no path points to it and that no process runs from it. A delete of untracked files cannot be undone.

## Note for agents

```markdown
Docs in progress live in `<folder>/`. Finished docs and their state files live in
`<folder>/archive/`. `<folder>/.ignore` hides that folder from ripgrep. To search it, pass the
path: `rg <pattern> <folder>/archive/`.

To archive a doc, `git mv` it and its sidecar files there, then fix the paths that point to it.
```

## Report

Answer first: how many units moved and how many stayed. Then one table: unit, verdict, the evidence in a few words. For each finished doc with open owner checks, name the checks. Name each link that was broken before the move, and each unclear unit with the question that would settle it. End with the undo command: `git mv <folder>/archive/<unit> <folder>/`.

## Limits

- The `.ignore` file hides the folder from ripgrep. Other search tools (an IDE index, a code graph, a glob tool) may still list the archive. Untested.
- The skill moves docs. It never deletes one.
