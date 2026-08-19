"""Check the slug rule, record parsing, and dead-pid filtering."""

from __future__ import annotations

import json
import os

import pytest

from cc_mirror.records import (
    STATUS_DEAD,
    RecordStore,
    SessionRecord,
    cwd_slug,
    group_records,
    parse_record,
    pid_alive,
    read_records,
)

from .conftest import write_record


class TestSlug:
    """Every non-alphanumeric character of the cwd becomes a dash."""

    def test_plain_path_with_underscore(self):
        assert cwd_slug("/home/john/tree_perception") == "-home-john-tree-perception"

    def test_worktree_path_keeps_the_double_dash(self):
        assert (
            cwd_slug("/home/john/pdf-grinder/.claude/worktrees/x")
            == "-home-john-pdf-grinder--claude-worktrees-x"
        )

    @pytest.mark.parametrize(
        "cwd,slug",
        [
            ("/home/john", "-home-john"),
            ("/home/john/me649-ws", "-home-john-me649-ws"),
            ("/home/john/IsaacSim-6.0.0", "-home-john-IsaacSim-6-0-0"),
            (
                "/home/john/OneDrive/profile/ga503+tax",
                "-home-john-OneDrive-profile-ga503-tax",
            ),
            ("/home/john/housing/.worktrees/audit", "-home-john-housing--worktrees-audit"),
        ],
    )
    def test_live_project_folder_names(self, cwd, slug):
        assert cwd_slug(cwd) == slug

    def test_case_is_preserved(self):
        assert cwd_slug("/home/john/PDFViewerEnhanced") == "-home-john-PDFViewerEnhanced"


class TestParseRecord:
    """A record turns into a SessionRecord, or into nothing when malformed."""

    def test_full_record(self):
        data = {
            "pid": 1463270,
            "sessionId": "9b3de748-55cd-46ff-98bc-25c272129f60",
            "cwd": "/home/john/pdf-grinder/.claude/worktrees/stage-1-engine-module",
            "startedAt": 1787109882339,
            "version": "2.1.235",
            "name": "pdf-grinder-c3",
            "status": "waiting",
            "updatedAt": 1787150108795,
            "waitingFor": "input needed",
            "messagingSocketPath": "/run/user/1000/cc-socks/1463270.sock",
        }
        record = parse_record(data, alive=True)
        assert record is not None
        assert record.pid == 1463270
        assert record.status == "waiting"
        assert record.waiting_for == "input needed"
        assert record.started_at == pytest.approx(1787109882.339)
        assert record.slug == "-home-john-pdf-grinder--claude-worktrees-stage-1-engine-module"
        assert record.folder == "stage-1-engine-module"
        assert record.short_id == "c3"
        assert record.transcript_path.name == "9b3de748-55cd-46ff-98bc-25c272129f60.jsonl"

    def test_missing_fields_are_rejected(self):
        assert parse_record({"pid": 1}) is None
        assert parse_record({"sessionId": "x", "cwd": "/tmp"}) is None
        assert parse_record({"pid": "not-an-int", "sessionId": "x", "cwd": "/t"}) is None

    def test_unknown_status_falls_back_to_idle(self):
        record = parse_record(
            {"pid": 5, "sessionId": "s", "cwd": "/tmp", "status": "nonsense"}, alive=True
        )
        assert record.status == "idle"

    def test_dead_pid_reports_status_dead(self):
        record = parse_record(
            {"pid": 5, "sessionId": "s", "cwd": "/tmp", "status": "busy"}, alive=False
        )
        assert record.status == "busy"
        assert record.display_status == STATUS_DEAD


class TestPidAlive:
    """A live pid is the one this test runs under."""

    def test_own_pid_is_alive(self):
        assert pid_alive(os.getpid()) is True

    def test_impossible_pid_is_dead(self):
        assert pid_alive(0) is False
        assert pid_alive(-1) is False
        assert pid_alive(4_194_303) is False


class TestReadRecords:
    """Records are read from disk and bad files are skipped."""

    def test_reads_every_valid_record(self, tmp_path):
        write_record(tmp_path, pid=os.getpid(), name="alive-aa")
        write_record(tmp_path, pid=4_194_303, name="dead-bb")
        (tmp_path / "broken.json").write_text("{not json")
        records = read_records(tmp_path)
        assert {r.name for r in records} == {"alive-aa", "dead-bb"}

    def test_missing_directory_is_empty(self, tmp_path):
        assert read_records(tmp_path / "nope") == []


class TestDeadFiltering:
    """A dead record stays for the grace time and then disappears."""

    def test_dead_record_is_kept_then_dropped(self, tmp_path):
        write_record(tmp_path, pid=os.getpid(), name="alive-aa")
        write_record(tmp_path, pid=4_194_303, name="dead-bb")
        store = RecordStore(tmp_path, grace_seconds=60.0)

        first = store.poll(now=1000.0)
        assert {r.name for r in first} == {"alive-aa", "dead-bb"}
        dead = [r for r in first if r.name == "dead-bb"][0]
        assert dead.display_status == STATUS_DEAD
        assert dead.dead_since == 1000.0

        still = store.poll(now=1059.0)
        assert "dead-bb" in {r.name for r in still}

        gone = store.poll(now=1061.0)
        assert {r.name for r in gone} == {"alive-aa"}

    def test_live_record_never_gets_a_dead_stamp(self, tmp_path):
        write_record(tmp_path, pid=os.getpid(), name="alive-aa")
        store = RecordStore(tmp_path)
        record = store.poll(now=1000.0)[0]
        assert record.dead_since is None
        assert record.display_status == "busy"


class TestGrouping:
    """Groups sort alphabetically and sessions sort by start time."""

    def _record(self, pid, cwd, started):
        return SessionRecord(
            pid=pid,
            session_id=f"s{pid}",
            cwd=cwd,
            name=f"n{pid}",
            status="busy",
            started_at=started,
            updated_at=started,
        )

    def test_stable_order(self):
        records = [
            self._record(3, "/home/john/zeta", 30.0),
            self._record(1, "/home/john/alpha", 20.0),
            self._record(2, "/home/john/alpha", 10.0),
        ]
        grouped = group_records(records)
        assert [cwd for cwd, _ in grouped] == ["/home/john/alpha", "/home/john/zeta"]
        assert [r.pid for r in grouped[0][1]] == [2, 1]

    def test_order_does_not_follow_status_changes(self, tmp_path):
        write_record(tmp_path, pid=os.getpid(), name="a-aa", cwd="/x", started_at=1)
        path = write_record(
            tmp_path, pid=os.getpid() + 0, name="a-aa", cwd="/x", started_at=1
        )
        data = json.loads(path.read_text())
        data["status"] = "waiting"
        path.write_text(json.dumps(data))
        store = RecordStore(tmp_path)
        before = [r.pid for r in store.poll(now=1.0)]
        after = [r.pid for r in store.poll(now=2.0)]
        assert before == after
