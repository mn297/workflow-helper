"""Read the tail of a Claude Code JSONL transcript."""

from __future__ import annotations

import json
from pathlib import Path

#: Bytes read from the end of a transcript. Enough for many turns, cheap to poll.
TAIL_BYTES = 262_144


def read_tail_lines(path: Path, tail_bytes: int = TAIL_BYTES) -> list[dict]:
    """Read the last chunk of a transcript and decode its whole JSON lines."""
    try:
        size = path.stat().st_size
    except OSError:
        return []
    try:
        with path.open("rb") as handle:
            if size > tail_bytes:
                handle.seek(size - tail_bytes)
                handle.readline()  # drop the partial first line
            raw = handle.read()
    except OSError:
        return []
    out: list[dict] = []
    for chunk in raw.split(b"\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            event = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(event, dict):
            out.append(event)
    return out


def read_all_lines(path: Path) -> list[dict]:
    """Read and decode every JSON line of a transcript."""
    out: list[dict] = []
    try:
        with path.open("r", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict):
                    out.append(event)
    except OSError:
        return out
    return out


def transcript_mtime(path: Path) -> float:
    """Give the transcript modification time, or 0 when it is missing."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
