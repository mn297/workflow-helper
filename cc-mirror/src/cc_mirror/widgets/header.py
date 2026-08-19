"""Show the session totals and jump to the next waiting session."""

from __future__ import annotations

from rich.text import Text
from textual.events import Click
from textual.widgets import Static

from ..messages import JumpToWaiting


class MirrorHeader(Static):
    """Show `N sessions · M waiting` and jump on click."""

    def __init__(self) -> None:
        super().__init__(id="header")
        self._summary = "0 sessions · 0 waiting"
        self._waiting = 0

    def set_summary(self, summary: str, waiting: int) -> None:
        """Update the totals line and the waiting highlight."""
        if summary == self._summary and waiting == self._waiting:
            return
        self._summary = summary
        self._waiting = waiting
        self.set_class(waiting > 0, "-has-waiting")
        self.update(self.render_summary())

    def render_summary(self) -> Text:
        """Build the header line."""
        text = Text()
        text.append(" CC MIRROR ", style="bold")
        text.append("── ", style="dim")
        text.append(self._summary, style="bold orange1" if self._waiting else "")
        if self._waiting:
            text.append("  ← click or press w to jump", style="dim")
        text.append(
            "   Enter opens · Ctrl+Q closes · q quits", style="dim"
        )
        return text

    def on_mount(self) -> None:
        """Paint the first header line."""
        self.update(self.render_summary())

    def on_click(self, event: Click) -> None:
        """Jump to the next waiting session on a header click."""
        event.stop()
        self.post_message(JumpToWaiting())
