"""Carry session events between cc-mirror widgets."""

from __future__ import annotations

from textual.message import Message


class SessionFocused(Message):
    """Ask the app to make one session the current one."""

    def __init__(self, pid: int) -> None:
        self.pid = pid
        super().__init__()


class SessionOpened(Message):
    """Ask the app to open the center view on one session."""

    def __init__(self, pid: int) -> None:
        self.pid = pid
        super().__init__()


class AgentsToggled(Message):
    """Ask the app to expand or collapse one session's agent tree."""

    def __init__(self, pid: int) -> None:
        self.pid = pid
        super().__init__()


class AgentOpened(Message):
    """Ask the app to open one subagent transcript."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__()


class CenterClosed(Message):
    """Ask the app to close the center view."""


class JumpToWaiting(Message):
    """Ask the app to move to the next session that needs a human."""
