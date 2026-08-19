"""Drive the whole dashboard against a real throwaway tmux session."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from cc_mirror import tmux as tmux_mod
from cc_mirror.app import CCMirrorApp
from cc_mirror.model import CLASS_TMUX
from cc_mirror.records import pid_alive
from cc_mirror.tmux import ancestors, list_panes
from cc_mirror.widgets.center import PaneMirror

from .conftest import screen_text, write_record

pytestmark = pytest.mark.skipif(
    not tmux_mod.tmux_available(), reason="tmux is not installed"
)

#: A stand-in for claude: prints a colored banner, then echoes what it reads.
READER = r"""
import sys
log = open(sys.argv[1], "a", buffering=1)
print("\033[36mCCMIRROR-CLAUDE-READY\033[0m", flush=True)
for line in sys.stdin:
    line = line.rstrip("\n")
    log.write(line + "\n")
    print("\033[32mECHO:" + line + "\033[0m", flush=True)
"""


def _tmux(*args: str) -> subprocess.CompletedProcess:
    """Run one tmux command for the fixture."""
    return subprocess.run(["tmux", *args], capture_output=True, text=True, timeout=5)


def _descendant(root: int, comm_prefix: str) -> int | None:
    """Find a process under a pid whose command name starts with a string."""
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            name = (entry / "comm").read_text().strip()
        except OSError:
            continue
        if name.startswith(comm_prefix) and root in ancestors(pid):
            return pid
    return None


@pytest.fixture
def fake_claude_session(tmp_path: Path):
    """Start a nested tmux process, write its record, then tear it all down."""
    name = f"cc-mirror-test-e2e-{os.getpid()}"
    log = tmp_path / "typed.txt"
    reader_py = tmp_path / "reader.py"
    reader_py.write_text(READER)
    sessions = tmp_path / "sessions"
    sessions.mkdir()

    # bash -> bash -> python gives the same shape as bash -> node -> claude.
    inner = f'python3 -u {reader_py} {log}; true'
    outer = f'bash --norc -c {subprocess.list2cmdline([inner])}; true'
    _tmux("new-session", "-d", "-s", name, "-x", "100", "-y", "30",
          "bash", "--norc", "-c", outer)
    time.sleep(0.8)

    panes = [p for p in list_panes() if p.session == name]
    if not panes:
        _tmux("kill-session", "-t", name)
        pytest.skip("could not start the throwaway tmux session")
    pane = panes[0]

    claude_pid = None
    deadline = time.time() + 3.0
    while time.time() < deadline and claude_pid is None:
        claude_pid = _descendant(pane.pane_pid, "python3")
        if claude_pid is None:
            time.sleep(0.1)
    if claude_pid is None:
        _tmux("kill-session", "-t", name)
        pytest.skip("the throwaway session never started its inner process")

    write_record(sessions, pid=claude_pid, name="demo-e2e",
                 cwd="/home/john/demo-e2e", status="busy",
                 session_id="99999999-9999-4999-8999-999999999999")
    try:
        yield sessions, pane, claude_pid, log
    finally:
        _tmux("kill-session", "-t", name)


class TestEndToEnd:
    """Records, pane matching, the live mirror, and typing all work together."""

    async def test_pid_matches_the_pane_through_two_levels(self, fake_claude_session):
        sessions, pane, claude_pid, _log = fake_claude_session
        assert pane.pane_pid in ancestors(claude_pid)
        assert pane.pane_pid != claude_pid
        matched = tmux_mod.find_pane_for_pid(claude_pid)
        assert matched is not None and matched.pane_id == pane.pane_id

    async def test_the_session_shows_as_a_tmux_class(self, fake_claude_session):
        sessions, pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            state = app.mirror.find(claude_pid)
            assert state is not None
            assert state.session_class == CLASS_TMUX
            assert state.pane.pane_id == pane.pane_id
            box = app.previews.box_for(claude_pid)
            assert not box.has_class("-ro")
            assert box.has_class("-busy")

    async def test_double_click_mirrors_the_real_screen(self, fake_claude_session):
        sessions, _pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{claude_pid}")
            await pilot.pause()
            assert app.center.mode == "live"
            assert "CCMIRROR-CLAUDE-READY" in screen_text(app)
            app.query_one(PaneMirror).stop()

    async def test_enter_opens_the_mirror_on_the_focused_box(self, fake_claude_session):
        sessions, _pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(claude_pid).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.mode == "live"
            assert app.center.pid == claude_pid
            assert "CCMIRROR-CLAUDE-READY" in screen_text(app)
            app.query_one(PaneMirror).stop()

    async def test_enter_inside_the_mirror_submits_to_the_real_session(self, fake_claude_session):
        sessions, _pane, claude_pid, log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(claude_pid).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            await pilot.press(*"submitted", "enter")
            await pilot.pause()
            deadline = time.time() + 4.0
            while time.time() < deadline:
                if log.exists() and "submitted" in log.read_text():
                    break
                await pilot.pause()
                time.sleep(0.05)
            assert "submitted" in log.read_text()
            assert app.center.is_open is True
            app.query_one(PaneMirror).stop()

    async def test_typing_lands_in_the_real_session(self, fake_claude_session):
        sessions, _pane, claude_pid, log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{claude_pid}")
            await pilot.pause()
            await pilot.press(*"hello", "enter")
            await pilot.pause()

            deadline = time.time() + 4.0
            while time.time() < deadline:
                if log.exists() and "hello" in log.read_text():
                    break
                await pilot.pause()
                time.sleep(0.05)
            assert "hello" in log.read_text()

            # The mirror picks the echo up on its next 100 ms poll.
            deadline = time.time() + 4.0
            while time.time() < deadline:
                if "ECHO:hello" in screen_text(app):
                    break
                await pilot.pause()
                time.sleep(0.05)
            assert "ECHO:hello" in screen_text(app)
            app.query_one(PaneMirror).stop()

    async def test_tmux_reports_a_cursor_for_the_real_pane(self, fake_claude_session):
        _sessions, pane, _claude_pid, _log = fake_claude_session
        cursor = tmux_mod.pane_cursor(pane.target)
        assert cursor is not None
        assert cursor.x >= 0 and cursor.y >= 0
        assert cursor.visible is True
        capture, batched = tmux_mod.capture_with_cursor(pane.target)
        assert "CCMIRROR-CLAUDE-READY" in capture
        assert batched is not None
        assert tmux_mod.CURSOR_SENTINEL not in capture

    async def test_the_cursor_advances_as_characters_are_typed(self, fake_claude_session):
        _sessions, pane, _claude_pid, _log = fake_claude_session
        before = tmux_mod.pane_cursor(pane.target)
        assert tmux_mod.send_text(pane.target, "abcde") is True
        deadline = time.time() + 3.0
        after = before
        while time.time() < deadline:
            after = tmux_mod.pane_cursor(pane.target)
            if after and after.x >= before.x + 5:
                break
            time.sleep(0.05)
        assert after.x == before.x + 5, f"{before} -> {after}"
        # Leave the pane's line clean for any later assertion.
        tmux_mod.send_key(pane.target, "C-u")

    async def test_the_overlay_follows_the_real_cursor(self, fake_claude_session):
        sessions, pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{claude_pid}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            assert mirror.shows_cursor is True

            def painted_cursor_column():
                """Give the column the overlay currently marks, if it is lit."""
                spans = mirror.cursor_spans
                if not spans or mirror.painted is None:
                    return None
                start = spans[0][0]
                line_start = mirror.painted.plain.rfind("\n", 0, start) + 1
                return start - line_start

            await pilot.press(*"hey")
            deadline = time.time() + 5.0
            reported = None
            while time.time() < deadline:
                reported = tmux_mod.pane_cursor(pane.target)
                if reported and reported.x >= 3:
                    break
                await pilot.pause()
                time.sleep(0.05)
            assert reported is not None and reported.x >= 3

            # The mirror polls every 100 ms and blinks every 500 ms, so wait
            # for a lit phase whose overlay sits on the reported column.
            deadline = time.time() + 5.0
            column = None
            while time.time() < deadline:
                column = painted_cursor_column()
                if column == reported.x and mirror.cursor is not None:
                    break
                await pilot.pause()
                time.sleep(0.05)
            assert column == reported.x
            assert mirror.cursor.x == reported.x
            mirror.stop()

    async def test_the_exit_chord_returns_to_the_dashboard(self, fake_claude_session):
        sessions, _pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{claude_pid}")
            await pilot.pause()
            assert app.center.is_open is True
            await pilot.press("ctrl+backslash")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.query_one(PaneMirror).target is None
            assert "demo-e2e" in screen_text(app)

    async def test_a_dead_session_drops_out_of_the_dashboard(self, fake_claude_session):
        sessions, pane, claude_pid, _log = fake_claude_session
        app = CCMirrorApp(sessions_dir=sessions, auto_poll=False)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.previews.box_for(claude_pid) is not None
            _tmux("kill-session", "-t", pane.session)
            deadline = time.time() + 4.0
            while time.time() < deadline and pid_alive(claude_pid):
                time.sleep(0.05)
            now = time.time()
            await app.apply(app.mirror.poll(now=now))
            await pilot.pause()
            box = app.previews.box_for(claude_pid)
            assert box is not None and box.has_class("-dead")
            await app.apply(app.mirror.poll(now=now + 61.0))
            await pilot.pause()
            assert app.previews.box_for(claude_pid) is None
