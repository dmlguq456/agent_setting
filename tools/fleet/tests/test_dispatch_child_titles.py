#!/usr/bin/env python3
"""Hermetic unit tests — child-session sidecar titles adopted onto dispatch rows.

The title refresher schedules dispatched children like main sessions (user 2026-07-16);
`_adopt_child_titles` is the display half: the enriched child Session's title is copied
onto the DispatchJob row that represents it (is_child session rows are hidden), and
`_dispatch_row` prefers that title over the slug — same title → name → slug chain as
session rows. Stdlib unittest, no real ps/proc/home access.
"""
import os
import sys
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import collectors as fleet_collectors  # noqa: E402
from fleet import render                          # noqa: E402
from fleet.model import DispatchJob, Session      # noqa: E402


def _child(pid, cwd, title, harness="claude", sid=None):
    return Session(harness=harness, pid=pid, cwd=cwd, session_id=sid or "sid-%d" % pid,
                   slug=os.path.basename(cwd), liveness="working", is_child=True,
                   title=title)


def _row_text(j, **kw):
    segs = render._dispatch_row(j, **kw)
    return "".join(part for part, _key in segs)


class AdoptChildTitlesTest(unittest.TestCase):
    def test_pid_join_adopts_the_child_title(self):
        child = _child(42, "/work/agent_setting-wt/fix-x", "Fix flaky title refresher tests")
        job = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/tmp/elsewhere",
                          harness="claude", pid=42, is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual(job.title, "Fix flaky title refresher tests")

    def test_cwd_join_adopts_when_pid_is_unknown(self):
        child = _child(42, "/work/agent_setting-wt/fix-x", "Port memory rows to board")
        job = DispatchJob(key="autopilot-code", slug="fix-x",
                          cwd="/work/agent_setting-wt/fix-x", harness="claude",
                          is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertEqual(job.title, "Port memory rows to board")

    def test_cwd_join_requires_matching_harness(self):
        child = _child(42, "/work/agent_setting-wt/fix-x", "Codex owns this cwd",
                       harness="codex")
        job = DispatchJob(key="autopilot-code", slug="fix-x",
                          cwd="/work/agent_setting-wt/fix-x", harness="claude",
                          is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertIsNone(job.title)

    def test_ambiguous_cwd_is_refused(self):
        # Two titled children in one cwd: adopting either would be a guess — F-26
        # (misattribution is worse than absence) keeps the slug.
        kids = [_child(1, "/work/shared", "First worker task"),
                _child(2, "/work/shared", "Second worker task")]
        job = DispatchJob(key="autopilot-code", slug="shared", cwd="/work/shared",
                          harness="claude", is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles(kids, [job])
        self.assertIsNone(job.title)

    def test_untitled_children_leave_the_job_untouched(self):
        child = _child(42, "/work/agent_setting-wt/fix-x", None)
        job = DispatchJob(key="autopilot-code", slug="fix-x", pid=42,
                          cwd="/work/agent_setting-wt/fix-x", harness="claude",
                          is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles([child], [job])
        self.assertIsNone(job.title)

    def test_main_session_titles_are_never_adopted(self):
        main = Session(harness="claude", pid=42, cwd="/work/agent_setting",
                       session_id="main-sid", slug="agent_setting", liveness="working",
                       title="Main session work")
        job = DispatchJob(key="autopilot-code", slug="fix-x", pid=42,
                          cwd="/work/agent_setting", harness="claude",
                          is_child=True, liveness="working")
        fleet_collectors._adopt_child_titles([main], [job])
        self.assertIsNone(job.title)


class DispatchRowTitleTest(unittest.TestCase):
    def test_wide_row_prefers_the_adopted_title_over_the_slug(self):
        job = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/w/fix-x",
                          harness="claude", is_child=True, liveness="working",
                          title="Fix refresher tests")
        text = _row_text(job)
        self.assertIn("Fix refresher tests", text)
        self.assertNotIn("fix-x", text.split("⎇")[0] if "⎇" in text else text)

    def test_wide_row_falls_back_to_the_slug_without_a_title(self):
        job = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/w/fix-x",
                          harness="claude", is_child=True, liveness="working")
        self.assertIn("fix-x", _row_text(job))

    def test_long_title_clips_inside_the_name_zone(self):
        long_title = "An extremely long haiku title that cannot possibly fit the name zone"
        job = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/w/fix-x",
                          harness="claude", is_child=True, liveness="working",
                          title=long_title)
        with_title = _row_text(job)
        job_slug = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/w/fix-x",
                               harness="claude", is_child=True, liveness="working")
        self.assertNotIn(long_title, with_title)
        self.assertIn("…", with_title)
        # The name zone budget is unchanged: a titled row is as long as a slug row.
        self.assertEqual(len(with_title), len(_row_text(job_slug)))

    def test_narrow_card_prefers_the_adopted_title(self):
        job = DispatchJob(key="autopilot-code", slug="fix-x", cwd="/w/fix-x",
                          harness="claude", is_child=True, liveness="working",
                          title="Narrow card title")
        l1, l2 = render._dispatch_row_2line(job)
        text = "".join(part for part, _key in l1 + l2)
        self.assertIn("Narrow card title", text)


if __name__ == "__main__":
    unittest.main()
