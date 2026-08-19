"""Find tmux panes and talk to them with capture-pane and send-keys."""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

#: Wait 150 ms between a typed line and its Enter (Ink paste-burst trap).
SUBMIT_DELAY_MS = 150

_PANE_FORMAT = "#{session_name}\t#{window_index}\t#{pane_index}\t#{pane_id}\t#{pane_pid}"

#: Textual key name -> tmux key name for keys that are not plain characters.
KEY_MAP = {
    "enter": "Enter",
    "return": "Enter",
    "escape": "Escape",
    "tab": "Tab",
    "shift+tab": "BTab",
    "backtab": "BTab",
    "backspace": "BSpace",
    "delete": "DC",
    "insert": "IC",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "page_up": "PageUp",
    "pagedown": "PageDown",
    "page_down": "PageDown",
    "space": "Space",
    "shift+up": "S-Up",
    "shift+down": "S-Down",
    "shift+left": "S-Left",
    "shift+right": "S-Right",
}


@dataclass(frozen=True)
class Pane:
    """Hold one tmux pane and the pid of the shell it runs."""

    session: str
    window: str
    index: str
    pane_id: str
    pane_pid: int

    @property
    def target(self) -> str:
        """Give the -t argument that names this pane."""
        return self.pane_id


def tmux_available() -> bool:
    """Say whether a tmux binary is on PATH."""
    return shutil.which("tmux") is not None


def _tmux(*args: str, timeout: float = 2.0) -> subprocess.CompletedProcess:
    """Run one tmux command and hand back the completed process."""
    return subprocess.run(
        ["tmux", *args],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
    )


def list_panes() -> list[Pane]:
    """List every pane on the running tmux server."""
    if not tmux_available():
        return []
    try:
        proc = _tmux("list-panes", "-a", "-F", _PANE_FORMAT)
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    panes: list[Pane] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        session, window, index, pane_id, pane_pid = parts
        try:
            pid = int(pane_pid)
        except ValueError:
            continue
        panes.append(Pane(session, window, index, pane_id, pid))
    return panes


def parent_pid(pid: int) -> int | None:
    """Read the parent pid of a process from /proc."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    close = raw.rfind(")")
    if close < 0:
        return None
    fields = raw[close + 2 :].split()
    if len(fields) < 2:
        return None
    try:
        return int(fields[1])
    except ValueError:
        return None


def ancestors(pid: int, limit: int = 64) -> list[int]:
    """Walk /proc upward from a pid and list its ancestors."""
    chain: list[int] = []
    current = parent_pid(pid)
    seen = {pid}
    while current and current > 0 and current not in seen and len(chain) < limit:
        chain.append(current)
        seen.add(current)
        current = parent_pid(current)
    return chain


def find_pane_for_pid(pid: int, panes: list[Pane] | None = None) -> Pane | None:
    """Match a Claude pid to the pane whose shell is one of its ancestors."""
    panes = list_panes() if panes is None else panes
    if not panes:
        return None
    by_pid = {pane.pane_pid: pane for pane in panes}
    if pid in by_pid:
        return by_pid[pid]
    for ancestor in ancestors(pid):
        pane = by_pid.get(ancestor)
        if pane is not None:
            return pane
    return None


def pane_map(pids: list[int]) -> dict[int, Pane]:
    """Match many Claude pids to panes in one pass over /proc."""
    panes = list_panes()
    if not panes:
        return {}
    out: dict[int, Pane] = {}
    for pid in pids:
        pane = find_pane_for_pid(pid, panes)
        if pane is not None:
            out[pid] = pane
    return out


@dataclass(frozen=True)
class Cursor:
    """Hold where a pane's cursor sits and whether the pane shows it."""

    x: int
    y: int
    visible: bool = True


#: Marks the cursor report that follows a capture in one batched tmux call.
#: Printable on purpose: tmux rewrites control bytes in a format string, and
#: the report is always last, so the final match is always the real one.
CURSOR_SENTINEL = "@@cc-mirror-cursor@@"
_CURSOR_FORMAT = CURSOR_SENTINEL + "#{cursor_x},#{cursor_y},#{cursor_flag}"


def parse_cursor(report: str) -> Cursor | None:
    """Read a `x,y,flag` cursor report from tmux."""
    parts = report.strip().split(",")
    if len(parts) != 3:
        return None
    try:
        x, y, flag = (int(p) for p in parts)
    except ValueError:
        return None
    if x < 0 or y < 0:
        return None
    return Cursor(x=x, y=y, visible=bool(flag))


def pane_cursor(target: str) -> Cursor | None:
    """Ask tmux where a pane's cursor is."""
    try:
        proc = _tmux("display-message", "-p", "-t", target, _CURSOR_FORMAT)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return parse_cursor(proc.stdout.replace(CURSOR_SENTINEL, ""))


def split_capture(stdout: str) -> tuple[str, Cursor | None]:
    """Split a batched tmux reply into the screen and the cursor report."""
    marker = stdout.rfind(CURSOR_SENTINEL)
    if marker < 0:
        return stdout, None
    capture = stdout[:marker]
    capture = capture.removesuffix("\n")
    return capture, parse_cursor(stdout[marker + len(CURSOR_SENTINEL) :])


def capture_with_cursor(target: str) -> tuple[str, Cursor | None]:
    """Capture a pane and read its cursor in one tmux call."""
    try:
        proc = _tmux(
            "capture-pane", "-e", "-p", "-t", target,
            ";",
            "display-message", "-p", "-t", target, _CURSOR_FORMAT,
        )
    except (OSError, subprocess.SubprocessError):
        return "", None
    if proc.returncode != 0:
        return "", None
    return split_capture(proc.stdout)


def capture_pane(target: str, escapes: bool = True) -> str:
    """Capture the rendered screen of a pane, colors included."""
    args = ["capture-pane", "-p", "-t", target]
    if escapes:
        args.insert(1, "-e")
    try:
        proc = _tmux(*args)
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


def pane_exists(target: str) -> bool:
    """Say whether a pane target still resolves on the server."""
    try:
        proc = _tmux("list-panes", "-a", "-F", "#{pane_id}")
    except (OSError, subprocess.SubprocessError):
        return False
    if proc.returncode != 0:
        return False
    return target in proc.stdout.split()


def send_text(target: str, text: str) -> bool:
    """Send text to a pane literally, with no key-name interpretation."""
    if not text:
        return True
    try:
        proc = _tmux("send-keys", "-t", target, "-l", text)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def send_key(target: str, key: str) -> bool:
    """Send one named key, such as Enter or C-c, to a pane."""
    try:
        proc = _tmux("send-keys", "-t", target, key)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def send_line(target: str, text: str, delay_ms: int = SUBMIT_DELAY_MS) -> bool:
    """Type a line, pause 150 ms, then send Enter to submit it."""
    if not send_text(target, text):
        return False
    time.sleep(delay_ms / 1000.0)
    return send_key(target, "Enter")


def tmux_key_name(key: str, character: str | None = None) -> tuple[str, str] | None:
    """Translate a Textual key into a tmux ("literal"|"key", value) pair."""
    if character is not None and len(character) == 1 and character.isprintable():
        return ("literal", character)
    lowered = key.lower()
    mapped = KEY_MAP.get(lowered)
    if mapped:
        return ("key", mapped)
    if lowered.startswith("ctrl+") and len(lowered) > 5:
        rest = lowered[5:]
        if len(rest) == 1:
            return ("key", f"C-{rest}")
        inner = tmux_key_name(rest)
        if inner and inner[0] == "key":
            return ("key", f"C-{inner[1]}")
    for prefix in ("alt+", "meta+", "option+"):
        if lowered.startswith(prefix):
            rest = lowered[len(prefix) :]
            if len(rest) == 1:
                return ("key", f"M-{rest}")
            inner = tmux_key_name(rest)
            if inner and inner[0] == "key":
                return ("key", f"M-{inner[1]}")
    if lowered.startswith("f") and lowered[1:].isdigit():
        return ("key", lowered.upper())
    if len(key) == 1 and key.isprintable():
        return ("literal", key)
    return None


def forward_key(target: str, key: str, character: str | None = None) -> bool:
    """Forward one Textual key event straight into a tmux pane."""
    resolved = tmux_key_name(key, character)
    if resolved is None:
        return False
    kind, value = resolved
    if kind == "literal":
        return send_text(target, value)
    return send_key(target, value)
