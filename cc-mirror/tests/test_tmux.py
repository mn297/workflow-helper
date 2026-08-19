"""Check pane matching, key translation, and a real tmux round-trip."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from cc_mirror import tmux as tmux_mod
from cc_mirror.sender import PaneSender
from cc_mirror.tmux import (
    Pane,
    ancestors,
    capture_pane,
    find_pane_for_pid,
    forward_key,
    list_panes,
    parent_pid,
    send_key,
    send_text,
    tmux_key_name,
)

#: Every throwaway session this file makes carries this prefix.
TEST_SESSION_PREFIX = "cc-mirror-test-"

pytestmark_tmux = pytest.mark.skipif(
    not tmux_mod.tmux_available(), reason="tmux is not installed"
)


class TestKeyTranslation:
    """Textual key names become tmux key names or literal text."""

    @pytest.mark.parametrize(
        "key,character,expected",
        [
            ("a", "a", ("literal", "a")),
            ("space", " ", ("literal", " ")),
            ("question_mark", "?", ("literal", "?")),
            ("enter", "\r", ("key", "Enter")),
            ("escape", "\x1b", ("key", "Escape")),
            ("tab", "\t", ("key", "Tab")),
            ("backspace", None, ("key", "BSpace")),
            ("delete", None, ("key", "DC")),
            ("up", None, ("key", "Up")),
            ("pagedown", None, ("key", "PageDown")),
            ("shift+tab", None, ("key", "BTab")),
            ("ctrl+c", None, ("key", "C-c")),
            ("ctrl+r", None, ("key", "C-r")),
            ("ctrl+left", None, ("key", "C-Left")),
            ("alt+f", None, ("key", "M-f")),
            ("f5", None, ("key", "F5")),
        ],
    )
    def test_mapping(self, key, character, expected):
        assert tmux_key_name(key, character) == expected

    def test_enter_is_a_key_even_though_it_has_a_character(self):
        # \r is not printable, so it never becomes literal text.
        assert tmux_key_name("enter", "\r") == ("key", "Enter")

    def test_unknown_key_is_dropped(self):
        assert tmux_key_name("f13_something_odd", None) is None


class TestProcWalk:
    """Ancestors come from /proc and end at pid 1."""

    def test_parent_of_this_process(self):
        assert parent_pid(os.getpid()) == os.getppid()

    def test_parent_of_a_dead_pid(self):
        assert parent_pid(4_194_303) is None

    def test_ancestors_reach_init(self):
        chain = ancestors(os.getpid())
        assert os.getppid() in chain
        assert chain[-1] == 1


class TestPaneMatching:
    """A pid matches the pane whose shell is one of its ancestors."""

    def test_direct_pane_pid_match(self):
        pane = Pane("s", "0", "0", "%1", os.getpid())
        assert find_pane_for_pid(os.getpid(), [pane]) is pane

    def test_ancestor_match(self):
        pane = Pane("s", "0", "0", "%2", os.getppid())
        assert find_pane_for_pid(os.getpid(), [pane]) is pane

    def test_no_match(self):
        pane = Pane("s", "0", "0", "%3", 4_194_303)
        assert find_pane_for_pid(os.getpid(), [pane]) is None

    def test_empty_pane_list(self):
        assert find_pane_for_pid(os.getpid(), []) is None


class TestPaneSender:
    """Queued keystrokes reach tmux in the order they were typed."""

    def test_order_is_preserved(self, monkeypatch):
        calls: list[tuple] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: calls.append(("text", s)) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: calls.append(("key", k)) or True)
        monkeypatch.setattr(tmux_mod, "send_line", lambda t, s: calls.append(("line", s)) or True)
        sender = PaneSender("%0")
        sender.start()
        sender.text("hi")
        sender.key("enter", "\r")
        sender.key("a", "a")
        sender.line("submitted")
        sender.stop()
        assert calls == [
            ("text", "hi"),
            ("key", "Enter"),
            ("text", "a"),
            ("line", "submitted"),
        ]

    def test_a_failing_send_does_not_stop_the_queue(self, monkeypatch):
        seen: list[str] = []

        def boom(target, text):
            raise RuntimeError("pane died")

        monkeypatch.setattr(tmux_mod, "send_text", boom)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: seen.append(k) or True)
        sender = PaneSender("%0")
        sender.start()
        sender.text("hi")
        sender.key("enter", "\r")
        sender.stop()
        assert seen == ["Enter"]


class TestNoServer:
    """Every tmux call is safe when nothing answers."""

    def test_capture_of_a_bogus_target(self):
        assert capture_pane("%999999") == ""

    def test_send_to_a_bogus_target(self):
        assert send_text("%999999", "x") is False
        assert send_key("%999999", "Enter") is False

    def test_forward_of_an_unknown_key(self):
        assert forward_key("%999999", "f13_something_odd") is False


# --------------------------------------------------------------------------
# Integration: one throwaway session, killed by name at the end.
# --------------------------------------------------------------------------


def _tmux(*args: str) -> subprocess.CompletedProcess:
    """Run a tmux command for the test fixture."""
    return subprocess.run(["tmux", *args], capture_output=True, text=True, timeout=5)


@pytest.fixture
def throwaway_pane(tmp_path: Path):
    """Start a cc-mirror-test session, hand back its pane, then kill it."""
    name = f"{TEST_SESSION_PREFIX}{os.getpid()}"
    log = tmp_path / "echoed.txt"
    # bash -> bash -> sleep gives a two-level descendant to match against.
    inner = 'bash --norc -c "sleep 300; true" & '
    reader = (
        'printf "\\033[36mCCMIRROR-READY\\033[0m\\n"; '
        'while IFS= read -r line; do printf "ECHO:%s\\n" "$line"; '
        f'printf "%s\\n" "$line" >> {log}; done'
    )
    _tmux("new-session", "-d", "-s", name, "-x", "80", "-y", "24",
          "bash", "--norc", "-c", inner + reader)
    time.sleep(0.6)
    panes = [p for p in list_panes() if p.session == name]
    if not panes:
        _tmux("kill-session", "-t", name)
        pytest.skip("could not start the throwaway tmux session")
    try:
        yield panes[0], log
    finally:
        _tmux("kill-session", "-t", name)


@pytestmark_tmux
class TestTmuxRoundTrip:
    """capture-pane and send-keys work against a real throwaway session."""

    def test_capture_pane_returns_the_screen_with_colors(self, throwaway_pane):
        pane, _log = throwaway_pane
        screen = capture_pane(pane.target)
        assert "CCMIRROR-READY" in screen
        assert "\x1b[" in screen, "capture-pane -e should carry SGR escapes"
        plain = capture_pane(pane.target, escapes=False)
        assert "CCMIRROR-READY" in plain
        assert "\x1b[" not in plain

    def test_send_line_lands_in_the_session(self, throwaway_pane):
        pane, log = throwaway_pane
        assert tmux_mod.send_line(pane.target, "hello from cc-mirror") is True
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if log.exists() and "hello from cc-mirror" in log.read_text():
                break
            time.sleep(0.05)
        assert "hello from cc-mirror" in log.read_text()
        screen = capture_pane(pane.target)
        assert "ECHO:hello from cc-mirror" in screen

    def test_forward_key_types_characters_then_submits(self, throwaway_pane):
        pane, log = throwaway_pane
        for char in "typed":
            assert forward_key(pane.target, char, char) is True
        time.sleep(0.15)
        assert forward_key(pane.target, "enter", "\r") is True
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if log.exists() and "typed" in log.read_text():
                break
            time.sleep(0.05)
        assert "typed" in log.read_text()

    def test_pane_sender_delivers_from_its_thread(self, throwaway_pane):
        pane, log = throwaway_pane
        sender = PaneSender(pane.target)
        sender.start()
        sender.line("via the sender")
        sender.stop(timeout=3.0)
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if log.exists() and "via the sender" in log.read_text():
                break
            time.sleep(0.05)
        assert "via the sender" in log.read_text()

    def test_a_descendant_pid_matches_the_pane(self, throwaway_pane):
        pane, _log = throwaway_pane
        sleeper = _find_descendant(pane.pane_pid, "sleep")
        assert sleeper is not None, "the throwaway session should hold a sleep process"
        assert pane.pane_pid in ancestors(sleeper)
        found = find_pane_for_pid(sleeper)
        assert found is not None and found.pane_id == pane.pane_id

    def test_pane_exists_and_the_pane_shows_the_main_screen(self, throwaway_pane):
        pane, _log = throwaway_pane
        assert tmux_mod.pane_exists(pane.target) is True
        assert tmux_mod.pane_exists("%999999") is False
        alt = _tmux("display-message", "-p", "-t", pane.target, "#{alternate_on}")
        assert alt.stdout.strip() == "0"

    def test_only_the_throwaway_session_is_touched(self, throwaway_pane):
        pane, _log = throwaway_pane
        names = {p.session for p in list_panes()}
        assert pane.session in names
        assert not any(n.startswith("claude-retry-") for n in names if n == pane.session)


def _find_descendant(root: int, comm: str) -> int | None:
    """Find a process under a pid whose command name starts with a string."""
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            name = (entry / "comm").read_text().strip()
        except OSError:
            continue
        if not name.startswith(comm):
            continue
        if root in ancestors(pid):
            return pid
    return None
