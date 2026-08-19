"""Send keystrokes to one tmux pane in order, off the UI thread."""

from __future__ import annotations

import queue
import threading

from . import tmux as tmux_mod

_STOP = object()


class PaneSender:
    """Queue keystrokes for one pane and deliver them from a worker thread."""

    def __init__(self, target: str) -> None:
        self.target = target
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self.sent: list[tuple] = []

    def start(self) -> None:
        """Start the delivery thread."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="cc-mirror-send")
        self._thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        """Drain the queue and stop the delivery thread."""
        if self._thread is None:
            return
        self._queue.put(_STOP)
        self._thread.join(timeout=timeout)
        self._thread = None

    def _run(self) -> None:
        """Pop queued actions and hand them to tmux one at a time."""
        while True:
            item = self._queue.get()
            if item is _STOP:
                return
            action, payload = item
            try:
                if action == "key":
                    tmux_mod.forward_key(self.target, payload[0], payload[1])
                elif action == "text":
                    tmux_mod.send_text(self.target, payload)
                elif action == "line":
                    tmux_mod.send_line(self.target, payload)
            except Exception:  # a dead pane must not kill the sender
                continue

    def key(self, key: str, character: str | None = None) -> None:
        """Queue one key press."""
        self.sent.append(("key", key))
        self._queue.put(("key", (key, character)))

    def text(self, text: str) -> None:
        """Queue literal text."""
        self.sent.append(("text", text))
        self._queue.put(("text", text))

    def line(self, text: str) -> None:
        """Queue a line: text, a 150 ms pause, then Enter."""
        self.sent.append(("line", text))
        self._queue.put(("line", text))
