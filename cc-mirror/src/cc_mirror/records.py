"""Read session records from ~/.claude/sessions."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, replace
from pathlib import Path

SESSIONS_DIR = Path.home() / ".claude" / "sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

#: Seconds a dead record stays on screen before cc-mirror drops it.
DEAD_GRACE_SECONDS = 60.0

STATUS_BUSY = "busy"
STATUS_WAITING = "waiting"
STATUS_IDLE = "idle"
STATUS_DEAD = "dead"


def cwd_slug(cwd: str) -> str:
    """Turn a working directory into its ~/.claude/projects folder name."""
    return "".join(c if c.isalnum() else "-" for c in cwd)


def pid_alive(pid: int) -> bool:
    """Say whether a process id still exists."""
    if pid <= 0:
        return False
    return os.path.isdir(f"/proc/{pid}")


@dataclass(frozen=True)
class SessionRecord:
    """Hold one ~/.claude/sessions/<pid>.json record."""

    pid: int
    session_id: str
    cwd: str
    name: str
    status: str
    started_at: float
    updated_at: float
    version: str = ""
    waiting_for: str = ""
    messaging_socket_path: str = ""
    alive: bool = True
    #: Wall-clock time when cc-mirror first saw this record dead.
    dead_since: float | None = None

    @property
    def slug(self) -> str:
        """Give the ~/.claude/projects folder name for this session."""
        return cwd_slug(self.cwd)

    @property
    def transcript_path(self) -> Path:
        """Give the JSONL transcript path for this session."""
        return PROJECTS_DIR / self.slug / f"{self.session_id}.jsonl"

    @property
    def folder(self) -> str:
        """Give the short folder name used as the sidebar group label."""
        return Path(self.cwd).name or self.cwd

    @property
    def display_status(self) -> str:
        """Give the status to paint: dead beats the recorded status."""
        return STATUS_DEAD if not self.alive else self.status

    @property
    def short_id(self) -> str:
        """Give the trailing tag of the derived session name."""
        tail = self.name.rsplit("-", 1)[-1] if self.name else ""
        return tail or self.session_id[:2]


def parse_record(data: dict, *, alive: bool | None = None) -> SessionRecord | None:
    """Build a SessionRecord from decoded record JSON."""
    pid = data.get("pid")
    session_id = data.get("sessionId")
    cwd = data.get("cwd")
    if not isinstance(pid, int) or not session_id or not cwd:
        return None
    status = data.get("status") or STATUS_IDLE
    if status not in (STATUS_BUSY, STATUS_WAITING, STATUS_IDLE):
        status = STATUS_IDLE
    return SessionRecord(
        pid=pid,
        session_id=session_id,
        cwd=cwd,
        name=data.get("name") or session_id[:8],
        status=status,
        started_at=float(data.get("startedAt") or 0) / 1000.0,
        updated_at=float(data.get("updatedAt") or 0) / 1000.0,
        version=str(data.get("version") or ""),
        waiting_for=str(data.get("waitingFor") or ""),
        messaging_socket_path=str(data.get("messagingSocketPath") or ""),
        alive=pid_alive(pid) if alive is None else alive,
    )


def read_records(sessions_dir: Path | None = None) -> list[SessionRecord]:
    """Read every session record on disk, in filename order."""
    root = sessions_dir or SESSIONS_DIR
    out: list[SessionRecord] = []
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        record = parse_record(data)
        if record is not None:
            out.append(record)
    return out


def sort_key(record: SessionRecord) -> tuple:
    """Give the stable sidebar order: group by cwd, then by start time."""
    return (record.cwd, record.started_at, record.pid)


def group_records(records: list[SessionRecord]) -> list[tuple[str, list[SessionRecord]]]:
    """Group records by cwd, groups alphabetical and sessions by start time."""
    groups: dict[str, list[SessionRecord]] = {}
    for record in records:
        groups.setdefault(record.cwd, []).append(record)
    ordered: list[tuple[str, list[SessionRecord]]] = []
    for cwd in sorted(groups):
        members = sorted(groups[cwd], key=lambda r: (r.started_at, r.pid))
        ordered.append((cwd, members))
    return ordered


class RecordStore:
    """Track session records across polls and time out the dead ones."""

    def __init__(
        self,
        sessions_dir: Path | None = None,
        grace_seconds: float = DEAD_GRACE_SECONDS,
    ) -> None:
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        self.grace_seconds = grace_seconds
        self._dead_since: dict[int, float] = {}

    def poll(self, now: float | None = None) -> list[SessionRecord]:
        """Re-read the records and drop pids dead longer than the grace time."""
        now = time.time() if now is None else now
        fresh = read_records(self.sessions_dir)
        kept: list[SessionRecord] = []
        seen: set[int] = set()
        for record in fresh:
            seen.add(record.pid)
            if record.alive:
                self._dead_since.pop(record.pid, None)
                kept.append(record)
                continue
            first_seen = self._dead_since.setdefault(record.pid, now)
            if now - first_seen >= self.grace_seconds:
                continue
            kept.append(replace(record, dead_since=first_seen))
        for pid in list(self._dead_since):
            if pid not in seen:
                del self._dead_since[pid]
        return sorted(kept, key=sort_key)
