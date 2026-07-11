#!/usr/bin/env python3
"""F-19 (메모리 관측 패널) — hermetic unit tests.

Runnable directly or via `python3 -m unittest fleet.tests.test_f19_memory -v` (from `tools/`).
"""
import datetime
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import render                        # noqa: E402
from fleet.collectors import memory as memcol   # noqa: E402


def _write_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


class _TmpStoreCase(unittest.TestCase):
    """Isolates every test behind its own MEM_STORE/MEM_WRITE_EVENTS — never touches the
    real ~/.local/state or ~/agent_setting journal (mirrors the 2026-07-11 실유출 회귀 fix)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Path(self._tmp.name) / "memory"
        self.store.mkdir(parents=True)
        self._env = mock.patch.dict(os.environ, {
            "MEM_STORE": str(self.store),
            "MEM_WRITE_EVENTS": str(self.store / "write-events.jsonl"),
        }, clear=False)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    @property
    def journal(self):
        return self.store / "write-events.jsonl"

    @property
    def graveyard(self):
        return self.store / "deleted-records.jsonl"


def _event(ts, action, tier="working", rtype="fact", actor="manual", snippet="x"):
    return json.dumps({"ts": ts, "action": action, "id": "id1", "tier": tier, "scope": "project",
                        "type": rtype, "actor": actor, "sid": "", "snippet": snippet})


def _grave(deleted_at, action):
    return json.dumps({"id": "id1", "tier": "working", "scope": "project", "type": "fact",
                        "body": "x", "_deleted_at": deleted_at, "_action": action,
                        "_canonical": None})


class JournalParseTest(_TmpStoreCase):
    def test_absent_files_return_none(self):
        self.assertIsNone(memcol.collect())

    def test_journal_only_aggregates_today(self):
        now = datetime.datetime(2026, 7, 11, 18, 0, 0)
        _write_lines(self.journal, [
            _event("2026-07-11T09:00:00", "add", tier="working"),
            _event("2026-07-11T09:05:00", "add", tier="durable"),
            _event("2026-07-11T09:06:00", "note", tier="working"),
            _event("2026-07-11T10:00:00", "lifecycle-expire"),
            _event("2026-07-11T11:00:00", "prune"),
            _event("2026-07-10T23:00:00", "add", tier="working"),  # yesterday — excluded
            _event("2026-07-11T12:00:00", "add", tier="working", actor="distiller"),
        ])
        result = memcol.collect(now=now)
        self.assertIsNotNone(result)
        today = result["today"]
        self.assertEqual(today["added_working"], 3)
        self.assertEqual(today["added_durable"], 1)
        self.assertEqual(today["added"], 4)
        self.assertEqual(today["expired"], 1)
        self.assertEqual(today["pruned"], 1)
        self.assertEqual(result["last_distill_min"], 360)   # 18:00 - 12:00 = 6h

    def test_malformed_lines_are_skipped(self):
        now = datetime.datetime(2026, 7, 11, 12, 0, 0)
        _write_lines(self.journal, [
            "{not json",
            _event("2026-07-11T09:00:00", "add"),
            "",
            "null",
            "42",
        ])
        result = memcol.collect(now=now)
        self.assertEqual(result["today"]["added"], 1)

    def test_journal_absent_graveyard_only_degrades(self):
        now = datetime.datetime(2026, 7, 11, 12, 0, 0)
        _write_lines(self.graveyard, [
            _grave("2026-07-11T09:00:00", "prune"),
            _grave("2026-07-11T10:00:00", "lifecycle-expire"),
            _grave("2026-07-10T09:00:00", "prune"),  # yesterday — excluded
        ])
        result = memcol.collect(now=now)
        self.assertIsNotNone(result)
        self.assertFalse(result["journal_available"])
        self.assertTrue(result["graveyard_available"])
        self.assertEqual(result["today"]["added"], 0)   # unknowable without the journal
        self.assertEqual(result["today"]["expired"], 1)
        self.assertEqual(result["today"]["pruned"], 1)
        self.assertIsNone(result["last_distill_min"])   # actor not in graveyard rows

    def test_recent_events_newest_first_capped_at_8(self):
        now = datetime.datetime(2026, 7, 11, 12, 0, 0)
        _write_lines(self.journal, [_event("2026-07-11T%02d:00:00" % h, "add") for h in range(10)])
        result = memcol.collect(now=now)
        self.assertEqual(len(result["recent"]), 8)
        self.assertEqual(result["recent"][0]["ts"], "2026-07-11T09:00:00")   # last written = newest

    def test_distill_stale_flags_when_over_threshold(self):
        now = datetime.datetime(2026, 7, 12, 12, 0, 0)
        _write_lines(self.journal, [_event("2026-07-11T00:00:00", "add", actor="distiller")])
        result = memcol.collect(now=now)
        self.assertTrue(result["alerts"]["distill_stale"])

    def test_distill_not_stale_within_threshold(self):
        now = datetime.datetime(2026, 7, 11, 12, 0, 0)
        _write_lines(self.journal, [_event("2026-07-11T09:00:00", "add", actor="distiller")])
        result = memcol.collect(now=now)
        self.assertFalse(result["alerts"]["distill_stale"])


class DurableOverTest(_TmpStoreCase):
    def _make_db(self, rows):
        db = self.store / "memory.db"
        con = sqlite3.connect(str(db))
        con.execute("CREATE TABLE records (id TEXT, tier TEXT, scope TEXT, cwd_origin TEXT)")
        con.executemany("INSERT INTO records VALUES (?,?,?,?)", rows)
        con.commit()
        con.close()

    def test_over_ceiling_project_surfaces(self):
        rows = [("id%d" % i, "durable", "project", "proj-a") for i in range(85)]
        rows += [("id%d" % i, "durable", "project", "proj-b") for i in range(5)]
        self._make_db(rows)
        _write_lines(self.journal, [_event("2026-07-11T09:00:00", "add")])
        result = memcol.collect(now=datetime.datetime(2026, 7, 11, 12, 0, 0))
        over = dict(result["alerts"]["durable_over"])
        self.assertEqual(over.get("proj-a"), 85)
        self.assertNotIn("proj-b", over)

    def test_db_absent_degrades_to_empty(self):
        _write_lines(self.journal, [_event("2026-07-11T09:00:00", "add")])
        result = memcol.collect(now=datetime.datetime(2026, 7, 11, 12, 0, 0))
        self.assertEqual(result["alerts"]["durable_over"], [])

    def test_corrupt_db_degrades_to_empty(self):
        (self.store / "memory.db").write_text("not a sqlite file", encoding="utf-8")
        _write_lines(self.journal, [_event("2026-07-11T09:00:00", "add")])
        result = memcol.collect(now=datetime.datetime(2026, 7, 11, 12, 0, 0))
        self.assertEqual(result["alerts"]["durable_over"], [])


class RenderIntegrationTest(unittest.TestCase):
    """render._build_lines consumes the F-19 `memory` snapshot — purely in-memory, no I/O."""

    def tearDown(self):
        render.set_show_all(False)

    def _text(self, lines):
        return "\n".join("".join(t for t, _k in ln) for ln in lines if ln)

    def _snapshot(self, **over):
        base = {
            "journal_available": True, "graveyard_available": True,
            "today": {"added_working": 3, "added_durable": 1, "added": 4,
                      "expired": 2, "pruned": 1},
            "last_distill_min": 45,
            "recent": [{"ts": "2026-07-11T09:00:00", "action": "add", "tier": "working",
                       "type": "fact", "actor": "manual", "sid": "", "snippet": "hello"}],
            "alerts": {"durable_over": [], "distill_stale": False},
        }
        base.update(over)
        return base

    def test_none_memory_omits_row_and_never_raises(self):
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=None)
        self.assertNotIn("mem  +", self._text(lines))

    def test_healthy_zero_event_no_alert_row_omitted(self):
        snap = self._snapshot(today={"added_working": 0, "added_durable": 0, "added": 0,
                                      "expired": 0, "pruned": 0})
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=snap)
        self.assertNotIn("mem  +", self._text(lines))

    def test_summary_row_renders_counts(self):
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=self._snapshot())
        text = self._text(lines)
        self.assertIn("+4 added(3w·1d)", text)
        self.assertIn("2 expired", text)
        self.assertIn("1 pruned", text)
        self.assertIn("last distill 45m", text)

    def test_a_toggle_reveals_recent_events(self):
        render.set_show_all(True)
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=self._snapshot())
        text = self._text(lines)
        self.assertIn("hello", text)

    def test_a_toggle_off_hides_recent_events(self):
        render.set_show_all(False)
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=self._snapshot())
        self.assertNotIn("hello", self._text(lines))

    def test_durable_over_alert_bucket_appears(self):
        snap = self._snapshot(alerts={"durable_over": [["proj-a", 85]], "distill_stale": False})
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=snap)
        text = self._text(lines)
        self.assertIn("durable-over", text)
        self.assertIn("proj-a=85", text)

    def test_distill_stale_alert_bucket_appears(self):
        snap = self._snapshot(alerts={"durable_over": [], "distill_stale": True})
        lines = render._build_lines([], [], section="fleet", narrow=False, malformed=0,
                                    layout="wide", memory=snap)
        self.assertIn("distill stale", self._text(lines))


if __name__ == "__main__":
    unittest.main()
