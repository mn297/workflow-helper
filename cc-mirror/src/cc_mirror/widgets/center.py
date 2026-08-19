"""Mirror one session in a center overlay and type into it."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.text import Text
from textual.containers import Container, VerticalScroll
from textual.events import Key, Paste
from textual.widgets import Static

from .. import labels as labels_mod
from .. import screen as screen_mod
from .. import tmux as tmux_mod
from .. import transcript as transcript_mod
from ..messages import CenterClosed
from ..model import CLASS_TMUX, SessionState
from ..sender import PaneSender

#: Seconds between capture-pane polls.
POLL_SECONDS = 0.1

#: Polls per blink phase: 5 ticks of 100 ms gives a 500 ms on/off cursor.
BLINK_TICKS = 5

#: Keys that leave the center view and return to the dashboard.
#:
#: These are the only keys the live mirror keeps for itself. Every other key,
#: Ctrl+C and Ctrl+Z included, still goes to Claude.
EXIT_KEYS = frozenset({"ctrl+backslash", "ctrl+q"})


class PaneMirror(Static, can_focus=True):
    """Repaint one tmux pane every 100 ms and forward every key to it."""

    def __init__(self) -> None:
        super().__init__(id="pane-mirror", markup=False)
        self.target: str | None = None
        self.sender: PaneSender | None = None
        self.cursor: tmux_mod.Cursor | None = None
        self.painted: Text | None = None
        self._digest: int | None = None
        self._base_key: tuple | None = None
        self._base: Text | None = None
        self._offset: int | None = None
        self._paint_key: tuple | None = None
        self._timer = None
        self.tick = 0
        self.poll_count = 0
        self.repaint_count = 0
        #: How often the capture was parsed. A blink must never raise this.
        self.parse_count = 0

    def start(self, target: str) -> None:
        """Attach to a pane, paint it once, then poll it."""
        self.stop()
        self.target = target
        self._digest = None
        self._base_key = None
        self._paint_key = None
        self.tick = 0
        self.sender = PaneSender(target)
        self.sender.start()
        capture, cursor = tmux_mod.capture_with_cursor(target)
        self.paint(capture, cursor)
        self._timer = self.set_interval(POLL_SECONDS, self._poll)

    def pause_polling(self) -> None:
        """Stop the poll timer but stay attached to the pane."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def stop(self) -> None:
        """Detach from the pane and stop polling."""
        self.pause_polling()
        if self.sender is not None:
            self.sender.stop()
            self.sender = None
        self.target = None
        self.cursor = None

    @property
    def blink_on(self) -> bool:
        """Say whether the cursor shows on this poll tick."""
        return (self.tick // BLINK_TICKS) % 2 == 0

    @property
    def shows_cursor(self) -> bool:
        """Say whether this mirror should paint a cursor at all."""
        return self.has_focus and self.target is not None

    def content_digest(self, capture: str) -> int:
        """Hash the screen text alone, with no cursor or blink phase in it."""
        return hash(capture)

    def paint(self, capture: str, cursor: tmux_mod.Cursor | None = None) -> bool:
        """Repaint only when the screen, the cursor cell, or the blink changed."""
        digest = self.content_digest(capture)
        wanted = cursor if (cursor is not None and cursor.visible) else None
        if not self.shows_cursor:
            wanted = None
        lit = wanted is not None and self.blink_on
        paint_key = (digest, wanted.x if wanted else -1, wanted.y if wanted else -1, lit)
        if paint_key == self._paint_key:
            return False
        self._paint_key = paint_key
        self._digest = digest
        self.cursor = cursor

        base_key = (digest, wanted.x if wanted else -1, wanted.y if wanted else -1)
        if base_key != self._base_key:
            # Only a real screen or cursor-cell change re-parses the capture.
            self._base_key = base_key
            self._base, self._offset = screen_mod.prepare_text(capture, wanted)
            self.parse_count += 1
        self.repaint_count += 1
        self.painted = screen_mod.with_cursor(self._base, self._offset if lit else None)
        self.update(self.painted)
        return True

    @property
    def cursor_spans(self) -> list[tuple[int, int]]:
        """List the character ranges the cursor style covers right now."""
        if self.painted is None:
            return []
        return [
            (span.start, span.end)
            for span in self.painted.spans
            if screen_mod.CURSOR_STYLE in str(span.style)
        ]

    async def _poll(self) -> None:
        """Capture the pane off the event loop and repaint on a real change."""
        target = self.target
        if not target:
            return
        capture, cursor = await asyncio.to_thread(
            tmux_mod.capture_with_cursor, target
        )
        self.poll_count += 1
        self.tick += 1
        if self.target != target:
            return
        if not capture:
            alive = await asyncio.to_thread(tmux_mod.pane_exists, target)
            if not alive:
                self.post_message(CenterClosed())
                return
        self.paint(capture, cursor)

    def on_key(self, event: Key) -> None:
        """Forward every key to the pane, except the exit chords."""
        event.stop()
        event.prevent_default()
        if event.key in EXIT_KEYS:
            # Stolen before the sender ever sees it: Claude never gets these.
            self.post_message(CenterClosed())
            return
        if self.sender is not None:
            self.sender.key(event.key, event.character)

    def on_paste(self, event: Paste) -> None:
        """Forward a paste, submitting it when it ends in a newline."""
        event.stop()
        event.prevent_default()
        if self.sender is None:
            return
        text = event.text
        if text.endswith("\n"):
            self.sender.line(text.rstrip("\n"))
        else:
            self.sender.text(text)


class TranscriptView(VerticalScroll):
    """Show a read-only semantic transcript for a [ro] session."""

    def __init__(self) -> None:
        super().__init__(id="transcript-view")
        self.body = Static(id="transcript-body", markup=False)
        self.path: Path | None = None
        self.max_lines = 400
        self._mtime: float | None = None
        self.load_count = 0

    def compose(self):
        """Put the transcript body inside the scroll area."""
        yield self.body

    def load(self, state: SessionState, max_lines: int = 400) -> int:
        """Render the whole transcript of a session as semantic lines."""
        return self.load_path(state.record.transcript_path, max_lines)

    def follow(self) -> bool:
        """Re-read the transcript when the file grew, and report a reload."""
        if self.path is None:
            return False
        if transcript_mod.transcript_mtime(self.path) == self._mtime:
            return False
        self.load_path(self.path, self.max_lines)
        return True

    def load_path(self, path: Path, max_lines: int = 400) -> int:
        """Render any transcript file as semantic lines, newest at the end."""
        self.path = path
        self.max_lines = max_lines
        self._mtime = transcript_mod.transcript_mtime(path)
        self.load_count += 1
        # Keep following the tail only when the reader is already at the end.
        at_end = self.scroll_offset.y >= self.max_scroll_y
        events = transcript_mod.read_all_lines(path)
        lines: list[labels_mod.Label] = []
        for event in events:
            label = labels_mod.event_label(event)
            if label is None:
                continue
            if lines and lines[-1].text == label.text:
                continue
            lines.append(label)
        lines = lines[-max_lines:]
        text = Text()
        if not lines:
            text.append("(no transcript yet)", style="dim italic")
        for index, line in enumerate(lines):
            if index:
                text.append("\n")
            style = "bold" if line.kind == "prompt" else ("dim" if line.kind == "text" else "")
            text.append(line.text, style=style)
        self.body.update(text)
        if at_end:
            self.scroll_end(animate=False)
        return len(lines)


class CenterView(Container):
    """Hold the live pane mirror or the read-only transcript overlay."""

    def __init__(self) -> None:
        super().__init__(id="center")
        self.mirror = PaneMirror()
        self.transcript = TranscriptView()
        self.pid: int | None = None
        self.agent_id: str | None = None
        self.mode: str = ""

    def compose(self):
        """Put both center-view modes in place, one shown at a time."""
        yield self.mirror
        yield self.transcript

    def tick(self) -> bool:
        """Refresh a read-only view on the dashboard cadence."""
        if self.mode in ("transcript", "agent"):
            return self.transcript.follow()
        return False  # a live mirror runs its own 100 ms poll

    def on_mount(self) -> None:
        """Start hidden."""
        self.display = False
        self.mirror.display = False
        self.transcript.display = False

    def open(self, state: SessionState) -> str:
        """Open the overlay on a session and return the mode it used."""
        self.pid = state.record.pid
        self.agent_id = None
        self.display = True
        if state.session_class == CLASS_TMUX and state.pane is not None:
            self.mode = "live"
            self.transcript.display = False
            self.mirror.display = True
            self.border_title = f"{state.record.name} — LIVE"
            self.border_subtitle = "click outside · Ctrl+Q or Ctrl+\\ to close"
            self.mirror.start(state.pane.target)
            self.mirror.focus()
        else:
            self.mode = "transcript"
            self.mirror.stop()
            self.mirror.display = False
            self.transcript.display = True
            self.border_title = f"{state.record.name} — \\[ro] transcript"
            self.border_subtitle = "read only · click outside · Ctrl+Q to close"
            self.transcript.load(state)
            self.transcript.focus()
        self.add_class("-open")
        return self.mode

    def open_agent(self, agent) -> str:
        """Open the read-only transcript of one subagent."""
        self.pid = None
        self.agent_id = agent.agent_id
        self.mode = "agent"
        self.display = True
        self.mirror.stop()
        self.mirror.display = False
        self.transcript.display = True
        self.border_title = f"agent — {agent.title}"
        self.border_subtitle = f"{agent.state} · read only · Ctrl+Q to close"
        self.transcript.load_path(agent.path)
        self.transcript.focus()
        self.add_class("-open")
        return self.mode

    def close(self) -> None:
        """Close the overlay and release the pane."""
        self.agent_id = None
        self.mirror.stop()
        self.display = False
        self.mirror.display = False
        self.transcript.display = False
        self.remove_class("-open")
        self.pid = None
        self.mode = ""

    @property
    def is_open(self) -> bool:
        """Say whether the overlay is on screen."""
        return bool(self.display)
