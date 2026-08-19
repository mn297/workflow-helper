"""Start cc-mirror, or print the spike tables it was built on."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import labels as labels_mod
from . import tmux as tmux_mod
from . import transcript as transcript_mod
from .records import RecordStore, group_records, read_records


def _fmt_age(stamp: float) -> str:
    """Render a timestamp as a short age such as 12s or 4m."""
    if not stamp:
        return "-"
    delta = max(0.0, time.time() - stamp)
    if delta < 60:
        return f"{int(delta)}s"
    if delta < 3600:
        return f"{int(delta // 60)}m"
    return f"{int(delta // 3600)}h"


def cmd_records(args: argparse.Namespace) -> int:
    """Print the session record table (build step 1)."""
    store = RecordStore(grace_seconds=args.grace)
    records = store.poll() if not args.raw else read_records()
    if not records:
        print("no session records found")
        return 0
    header = f"{'PID':>8}  {'STATUS':<8}  {'NAME':<22}  {'AGE':>5}  {'CLASS':<8}  STARTED"
    panes = {}
    if tmux_mod.tmux_available():
        panes = tmux_mod.pane_map([r.pid for r in records if r.alive])
    for cwd, members in group_records(records):
        print(f"\n{cwd}")
        print(header)
        print("-" * len(header))
        for record in members:
            pane = panes.get(record.pid)
            started = time.strftime("%H:%M:%S", time.localtime(record.started_at))
            print(
                f"{record.pid:>8}  {record.display_status:<8}  {record.name:<22}  "
                f"{_fmt_age(record.updated_at):>5}  "
                f"{(pane.pane_id if pane else '[ro]'):<8}  {started}"
            )
    if args.verbose:
        print()
        for record in records:
            print(f"{record.name}: slug={record.slug}")
            print(f"  transcript={record.transcript_path}")
            print(f"  exists={record.transcript_path.exists()}")
    return 0


def cmd_labels(args: argparse.Namespace) -> int:
    """Print semantic preview lines for one or every session (build step 2)."""
    store = RecordStore(grace_seconds=args.grace)
    records = store.poll()
    if args.pid:
        records = [r for r in records if r.pid == args.pid]
        if not records:
            print(f"no record for pid {args.pid}", file=sys.stderr)
            return 1
    for record in records:
        path = record.transcript_path
        events = transcript_mod.read_tail_lines(path)
        print(f"== {record.name}  [{record.display_status}]  {record.cwd}")
        print(f"   slug: {record.slug}")
        print(f"   transcript: {path} ({'ok' if path.exists() else 'MISSING'}, "
              f"{len(events)} tail events)")
        for line in labels_mod.preview_lines(record, events):
            print(f"   {line.kind:<8} | {line.text}")
        print()
    return 0


def cmd_panes(args: argparse.Namespace) -> int:
    """Print the tmux panes and the Claude pids matched to them (build step 5)."""
    if not tmux_mod.tmux_available():
        print("tmux is not installed")
        return 1
    panes = tmux_mod.list_panes()
    if not panes:
        print("no tmux server running")
        return 0
    records = RecordStore().poll()
    matched = tmux_mod.pane_map([r.pid for r in records if r.alive])
    by_pane: dict[str, list[int]] = {}
    for pid, pane in matched.items():
        by_pane.setdefault(pane.pane_id, []).append(pid)
    print(f"{'PANE':<8}  {'SESSION':<28}  {'PANE_PID':>8}  CLAUDE_PIDS")
    for pane in panes:
        pids = ",".join(str(p) for p in by_pane.get(pane.pane_id, [])) or "-"
        print(f"{pane.pane_id:<8}  {pane.session:<28}  {pane.pane_pid:>8}  {pids}")
    return 0


def cmd_slug(args: argparse.Namespace) -> int:
    """Print the projects-folder slug for a working directory."""
    from .records import cwd_slug

    for path in args.paths:
        print(f"{path}\t{cwd_slug(path)}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Start the Textual dashboard."""
    from .app import CCMirrorApp

    app = CCMirrorApp(sessions_dir=Path(args.sessions_dir) if args.sessions_dir else None)
    app.run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the cc-mirror argument parser."""
    parser = argparse.ArgumentParser(
        prog="cc-mirror",
        description="Dashboard for every running Claude Code session.",
    )
    parser.add_argument(
        "--sessions-dir",
        default=None,
        help="read records from this directory instead of ~/.claude/sessions",
    )
    sub = parser.add_subparsers(dest="command")

    p_records = sub.add_parser("records", help="print the session record table")
    p_records.add_argument("--grace", type=float, default=60.0)
    p_records.add_argument("--raw", action="store_true", help="skip dead-pid filtering")
    p_records.add_argument("-v", "--verbose", action="store_true")
    p_records.set_defaults(func=cmd_records)

    p_labels = sub.add_parser("labels", help="print semantic preview lines")
    p_labels.add_argument("--grace", type=float, default=60.0)
    p_labels.add_argument("--pid", type=int, default=None)
    p_labels.set_defaults(func=cmd_labels)

    p_panes = sub.add_parser("panes", help="print tmux panes and matched pids")
    p_panes.set_defaults(func=cmd_panes)

    p_slug = sub.add_parser("slug", help="print the projects slug for a path")
    p_slug.add_argument("paths", nargs="+")
    p_slug.set_defaults(func=cmd_slug)

    p_run = sub.add_parser("run", help="start the dashboard (default)")
    p_run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the cc-mirror command line."""
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        return cmd_run(args)
    return func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
