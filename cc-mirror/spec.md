# cc-mirror

A mouse-first dashboard for all running Claude Code sessions. One command shows
every session. A double-click opens a live, typeable mirror of a session in a
large center view.

```text
$ cc-mirror
┌ CC MIRROR ── 4 sessions · 1 waiting ─────────────────────────────────┐
│┌ sidebar ─────────┐ ┌ previews (scroll) ─────────────────────────────┐│
││ pdf-grinder      │ │ ╔═ pdf-grinder-c3 ═══════════════ WAITING ═══╗ ││
││  ● c3  WAITING   │ │ ║ Approve: Bash(pytest)?                     ║ ││
││ tree_perception  │ │ ╚════════════════════════════════════════════╝ ││
││  ● e3  busy      │ │ ┌─ tree-perception-e3 ─────────────── busy ──┐ ││
││  ● fb  idle      │ │ │ Editing model.py…                          │ ││
││ cc-mirror        │ │ │ Bash(pytest -k fusion)                     │ ││
││  ● 5f  busy      │ │ └────────────────────────────────────────────┘ ││
│└──────────────────┘ │ ┌─ tree-perception-fb ─────────────── idle ──┐ ││
│                     │ │ Done: refactor complete                    │ ││
│                     │ └────────────────────────────────────────────┘ ││
└──────────────────────────────────────────────────────────────────────┘
```

Double-click a preview box:

```text
│┌ sidebar ────────┐ ╔═ tree-perception-e3 ═════════ LIVE ═════════════╗│
││ …               │ ║ (exact Claude screen, colors, 100 ms refresh)   ║│
││                 │ ║ > type here — keys go to the real session       ║│
│└─────────────────┘ ╚═════ click outside or Ctrl+\ to close ══════════╝│
```

## Foundation — what already exists (verified 2026-08-19)

| Source | Gives | Cost |
|---|---|---|
| `~/.claude/sessions/<pid>.json` | pid, sessionId, cwd, name, status (`busy` / `waiting` / `idle`), version | Claude Code ≥ 2.1.224 writes these itself |
| `~/.claude/projects/<cwd-slug>/<sessionId>.jsonl` | live transcript: prompts, responses, tool calls, tool results | appends in real time |
| `tmux capture-pane -e -p` | exact rendered screen with colors | tmux did the emulation |
| `tmux send-keys` | any keystroke into the session | zero code |

Traps, verified against live data:

- The cwd slug replaces EVERY non-alphanumeric character with `-`.
  `/home/john/tree_perception` → `-home-john-tree-perception`.
  `.claude` → `-claude` (double dash after the parent dir). Do not build the
  slug with a naive `/` replacement.
- `status: "waiting"` also covers a pending tool approval. The transcript then
  ends mid-turn on a `tool_result`, not on assistant text. Lead the preview
  with the status, not with the transcript tail.

## Two session classes

- **`[tmux]`** — the session is already inside tmux. Live center view and
  input.
- **`[ro]`** — a plain terminal (typical Cursor sessions). Preview and a
  read-only transcript view.

## Architecture

```text
~/.claude/sessions/*.json      → sidebar, status, counts
~/.claude/projects/**/*.jsonl  → preview lines (semantic)
tmux capture-pane / send-keys  → center view (raw, typeable)
        │
        ▼
  cc-mirror — Python, Textual
```

Framework is **Textual**: native mouse, double-click, wheel scroll, and CSS
layout. The old Node argument (shared types with an extension) died with the
extension.

## Layout

**Sidebar (left).** Sessions grouped by cwd, one group per folder. Order is
STABLE: groups alphabetical, sessions by start time. Color alone shows urgency
— the list never reorders under the mouse. Header shows totals:
`4 sessions · 1 waiting`. A hotkey and a header click jump to the next
`waiting` session.

**Preview stack (middle).** One box per session, vertical scroll. Each box
shows 3-5 semantic lines from the transcript: `Bash(git diff)`,
`Editing auth.ts…`, user prompt tails, `Done: <last text tail>`. For a
`waiting` session the first line is the pending question or approval.

**Center view (on double-click).** A large overlay box, not fullscreen. The
sidebar stays visible.

## States and outlines

| Record status | Label | Outline |
|---|---|---|
| `busy` | thinking | cyan |
| `waiting` | HUMAN NEEDED | orange, bold, double-line border |
| `idle` | idle | dim gray |
| record stale / pid dead | dead | dark, removed after 60 s |
| `[ro]` class | (any) | dashed border variant |

## Center view mechanics

1. Poll `tmux capture-pane -e -p -t <pane>` every 100 ms.
2. Hash the capture. Repaint only when the hash changes.
3. Forward every keystroke and paste with `send-keys -l`, special keys by
   name. For a submitted line, send text, wait 150 ms, then send Enter
   (Ink paste-burst trap: send text, wait, then Enter).
4. Exit: click outside the box, or `Ctrl+\`. All other keys belong to Claude.
5. Copy text out: Shift+drag (terminal-native selection bypass). No code.
6. `[ro]` sessions get a scrollable transcript render instead, read-only.

## Mouse and keys

| Input | Action |
|---|---|
| click box / sidebar row | focus session |
| double-click box | open center view |
| wheel | scroll preview stack; in center view, scroll transcript |
| `w` or header click | jump to next waiting session |
| `Ctrl+\` | close center view |
| `q` | quit (dashboard only, never inside center view) |

## Build order

Prove each step before the next. Steps 1-2 are the spike.

1. Script prints session records as a table, with dead-pid filtering.
2. Script tails one transcript and prints semantic labels. Test on the
   worktree slug case.
3. Textual shell: sidebar + scrollable preview stack, static data.
4. Live updates: watch records and transcripts, 1 s cadence.
5. pid → tmux pane matcher (`pane_pid` descendants).
6. Center view: capture-pane poll at 100 ms, hash-diff repaint.
7. Key forwarding with `send-keys`, exit chord, click-out.
8. `[ro]` transcript view, jump-to-waiting, polish.

## Future upgrades (not v1)

Ordered by expected value:

1. **Browser surface via `textual serve`** — Textual runs the same app in a
   browser tab over a local websocket. Zero rewrite. Also reachable from a
   phone on the LAN.
2. **Desktop notifications** — on a `busy` → `waiting` transition, fire
   `notify-send` with the session name and the pending question.
3. **tmux control mode (`tmux -C`)** — replace the 100 ms capture poll with
   event-driven output streaming. Removes the last latency.
4. **Approve/deny buttons** — a `waiting` preview box gets click targets that
   send the approval keys. Triage without opening the center view.
5. **Messaging socket** — each record advertises
   `messagingSocketPath` (`/run/user/1000/cc-socks/<pid>.sock`). Protocol not
   yet inspected. If it accepts structured input, it replaces `send-keys`.
6. **Web dashboard with xterm.js** — pixel-perfect live mirrors in a browser
   (xterm.js is a full terminal emulator; `ttyd` can serve a tmux session
   as-is). The escape hatch if terminal mouse UX disappoints.
7. **Ended-session browser** — transcripts outlive sessions; browse and search
   old JSONL.
8. **Remote machines** — same records and tmux over SSH.

## Non-goals

- VS Code/Cursor extension, proposed APIs, WebSocket transport
- own terminal emulation or ANSI parsing (tmux renders; capture is text+SGR)
- persistence, auth, cloud, remote machines, packaging
- retry and orchestration (`cs` owns queues)
- session spawning and recovery

## Definition of done

Five sessions run: some in tmux, some plain. `cc-mirror` shows all five,
grouped by folder, with correct status outlines, and previews update within
1 second. A `waiting` session stands out at a glance. Double-click on a
`[tmux]` session shows the exact Claude screen in the center box. Typing there
lands in the real session. `Ctrl+\` or a click outside returns to the
dashboard.
