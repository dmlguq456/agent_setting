"""D3 (v9) — fixed upper bound on the dispatch stage-zone breadcrumb (v8 discovery:
`_internal/test_reviews/test_review.md:89-110`, `final_report.md:51`).

168-col zero-overflow was previously incidental — a measured 5-cell slack, not a bound — so a
longer conductor/qa label or a further-along stage silently re-broke it. This suite pins the
cap structurally: mirrors test_f22_name_cap.py's width-test pattern (real render.py:44).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render                                     # noqa: E402
from fleet.model import DispatchJob                           # noqa: E402


def _job(key="code", worker_role="code-execute", stage="exec", slug="myslug", depth=1,
         liveness="working"):
    j = DispatchJob(key=key, slug=slug, stage=stage, depth=depth, liveness=liveness,
                    worker_role=worker_role)
    return j


def _segs_width(segs):
    return sum(render._dw(t) for t, _k in segs)


class StageZoneCapTest(unittest.TestCase):

    def test_cap_lives_in_exactly_one_constant(self):
        """Same idiom as _NAME_WIDE_MAX (test_f22_name_cap.py:44) — mutate, observe a real
        effect, restore. `stage="test"` gives two PAST stages (plan, exec) to fold, so a
        tighter cap visibly narrows the row without needing to touch the active stage."""
        self.assertEqual(render._STAGE_ZONE_MAX, 30)
        prev = render._STAGE_ZONE_MAX
        try:
            j = _job(key="code", worker_role=None, stage="test", slug="s")
            wide = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
            render._STAGE_ZONE_MAX = 14
            narrow = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
            self.assertLess(_segs_width(narrow), _segs_width(wide))
            self.assertLessEqual(_segs_width(narrow), 14)
        finally:
            render._STAGE_ZONE_MAX = prev

    def test_stage_zone_never_exceeds_the_cap(self):
        # every (key, stage) combo across every known pipeline, at every stage index.
        for key, seq in render._PIPE_STAGES.items():
            for stage in seq:
                j = _job(key=key, worker_role=None, stage=stage, slug="s")
                segs = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
                self.assertLessEqual(_segs_width(segs), render._STAGE_ZONE_MAX,
                                     "%s@%s exceeds the cap" % (key, stage))

    def test_long_conductor_label_is_dropped_not_tail_cut(self):
        """F-9(c) — a component (a whole past stage, or the role-label prefix) is dropped
        WHOLE; no label is ever emitted half-cut mid-word."""
        j = _job(key="code", worker_role="code-report", stage="report", slug="s")
        # code-report isn't a mid-pipeline stage — force an artificially long scenario by
        # widening the pipeline stub directly (a fixture-only pipeline, not a real one).
        prev = dict(render._PIPE_STAGES)
        try:
            render._PIPE_STAGES["fixture-long"] = [
                "alpha-phase-one", "beta-phase-two", "gamma-phase-three", "delta-phase-four"]
            j = _job(key="fixture-long", worker_role=None, stage="delta-phase-four", slug="s")
            segs = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
            self.assertLessEqual(_segs_width(segs), render._STAGE_ZONE_MAX)
            texts = [t for t, _k in segs]
            # no fragment ends mid-word with no ellipsis/separator boundary — every kept
            # label is a COMPLETE stage name (optionally +"✓") or the whole prefix, never a
            # partial substring of a longer one.
            known_words = {"alpha-phase-one✓", "beta-phase-two✓", "gamma-phase-three✓",
                           "delta-phase-four", " › ", "fixture-long: "}
            for t in texts:
                self.assertIn(t, known_words, "component은 통째로 살거나 죽어야 한다: %r" % t)
            self.assertIn("delta-phase-four", texts, "활성 스테이지가 드롭됐다")
        finally:
            render._PIPE_STAGES.clear()
            render._PIPE_STAGES.update(prev)

    def test_active_stage_survives_when_past_stages_drop(self):
        """SD-F2 — the active stage is the LAST thing dropped, never the first."""
        prev = render._STAGE_ZONE_MAX
        try:
            render._STAGE_ZONE_MAX = 12   # too tight for the full 3-stage breadcrumb
            j = _job(key="code", worker_role=None, stage="test", slug="s")
            segs = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
            joined = "".join(t for t, _k in segs)
            self.assertIn("test", joined, "활성 스테이지가 드롭됐다")
        finally:
            render._STAGE_ZONE_MAX = prev

    def test_168_no_overflow_is_structural_not_incidental(self):
        """★ D3's thesis — an artificially long role-suffix (unbounded in principle) must
        still respect the cap, not merely "happen to fit" at today's measured values."""
        j = _job(key="code", worker_role="code-execute:" + ("phase-" * 10) + "final",
                 stage="exec", slug="s")
        segs = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=True)
        self.assertLessEqual(_segs_width(segs), render._STAGE_ZONE_MAX)

    def test_short_rows_are_unaffected(self):
        """회귀 0 — a depth-1 row's full breadcrumb (19, 'plan✓ › exec › test') renders
        without any dropping triggered. 2026-07-20: the 'code: ' entry-skill prefix moved
        to the options dial (_entry_skill leads _opts_segs), so the breadcrumb is
        stages-only here; depth-2 stage workers keep their role-label prefix."""
        j = _job(key="code", worker_role="code-execute", stage="exec", slug="s")
        segs = render._dispatch_stage_segs(j, j.key, j.stage, j.slug, working=False)
        joined = "".join(t for t, _k in segs)
        self.assertEqual(joined, "plan✓ › exec › test")


class PrePlanBootTokenTest(unittest.TestCase):
    """user 2026-07-20: "plan 전에 이게 죽었나 살았나" — the unlit pre-plan track leads with a
    `pre` token carrying boot-phase liveness (blinks while working, dim while queued)."""

    def test_pre_leads_the_unlit_track_dim_when_not_working(self):
        segs = render._stage_segs("code", "open", working=False)
        self.assertEqual("".join(t for t, _k in segs), "pre › plan › exec › test")
        self.assertEqual(segs[0], ("pre", "stg0_off"))

    def test_pre_blinks_with_the_working_dot(self):
        prev = render._BLINK_ON
        try:
            render._BLINK_ON = True
            self.assertEqual(render._stage_segs("code", "", working=True)[0],
                             ("pre", "stg0_on"))
            render._BLINK_ON = False
            self.assertEqual(render._stage_segs("code", "", working=True)[0],
                             ("pre", "stg0_off"))
        finally:
            render._BLINK_ON = prev

    def test_pre_leaves_the_track_once_plan_lights(self):
        segs = render._stage_segs("code", "plan", working=True)
        self.assertNotIn("pre", "".join(t for t, _k in segs))


class StageZoneLeadInTest(unittest.TestCase):
    """user 2026-07-20: "stages 앞에 콜론 등으로 구분감" — dim ' : ' lead-in (leading space
    so an overflowing dial never glues to the colon), skipped when the breadcrumb brings
    its own colon."""

    def test_colon_leads_a_plain_breadcrumb(self):
        out = render._stage_zone_segs([("plan", "stg0_off")])
        self.assertEqual(out[0], (" : ", "dim"))

    def test_own_label_prefix_skips_the_colon(self):
        out = render._stage_zone_segs([("drill: ", "name_dim"), ("—", "dim")])
        self.assertEqual(out[0], ("  ", None))

    def test_empty_breadcrumb_gets_a_dash_placeholder(self):
        self.assertEqual(render._stage_zone_segs([]), [(" : ", "dim"), ("-", "dim")])

    def test_missing_stage_uses_ascii_dash(self):
        self.assertEqual(render._stage_segs("unknown", ""), [("-", "dim")])


if __name__ == "__main__":
    unittest.main()
