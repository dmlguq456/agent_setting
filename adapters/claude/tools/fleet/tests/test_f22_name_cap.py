"""F-22 minor (v8) — fixed upper bound on the wide-layout name zone (prd.md:218).

The v7 F-22 responsive name zone handed ALL leftover horizontal slack to the session
column, so a wide terminal stretched it without limit (measured pre-v8: 168 cols → 77
cells, 200 → 109). This suite pins the cap and, just as importantly, pins the things the
cap must NOT disturb.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render                                     # noqa: E402
from fleet.model import DispatchJob, Session                 # noqa: E402


class WideNameCapTest(unittest.TestCase):
    """The acceptance table (plan §5) — measured values, not asserted intent."""

    def test_acceptance_table(self):
        got = {w: render._wide_name_width(w) for w in (60, 120, 168, 200)}
        self.assertEqual(got, {60: 28, 120: 29, 168: 40, 200: 40})

    def test_narrow_widths_are_untouched_by_the_cap(self):
        """60 and 120 sit below the cap (28/29 < 40), so v8 must not move them at all."""
        for w in (60, 120):
            self.assertLess(render._wide_name_width(w), render._NAME_WIDE_MAX)

    def test_wide_widths_are_clamped_to_the_cap(self):
        for w in (168, 200, 400, 10000):
            self.assertEqual(render._wide_name_width(w), render._NAME_WIDE_MAX)

    def test_lower_bound_still_wins_on_tiny_terminals(self):
        """The floor outranks the cap — a 20-col terminal still gets _NW_S, not 20-ish."""
        for w in (1, 20, 40):
            self.assertEqual(render._wide_name_width(w), render._NW_S)

    def test_no_width_returns_the_static_default(self):
        self.assertEqual(render._wide_name_width(None), render._NW_S)
        self.assertEqual(render._wide_name_width(0), render._NW_S)

    def test_cap_lives_in_exactly_one_constant(self):
        """prd.md:218 — 'adjustable from one constant'."""
        self.assertEqual(render._NAME_WIDE_MAX, 40)
        prev = render._NAME_WIDE_MAX
        try:
            render._NAME_WIDE_MAX = 50
            self.assertEqual(render._wide_name_width(200), 50)
        finally:
            render._NAME_WIDE_MAX = prev
        self.assertEqual(render._wide_name_width(200), 40)

    def test_monotonic_and_never_negative(self):
        widths = [render._wide_name_width(w) for w in range(1, 400)]
        self.assertTrue(all(b >= a for a, b in zip(widths, widths[1:])), "not monotonic")
        self.assertTrue(all(w >= render._NW_S for w in widths))


class PreservedInvariantsTest(unittest.TestCase):
    """Things plan §5 explicitly says the cap must NOT change."""

    def test_legacy_none_width_path_keeps_the_24_cell_title_cap(self):
        """_session_row(name_width=None) → _TITLE_MAX clip (hermetic/legacy callers)."""
        s = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="proj",
                    title="A very long session title that would overflow any narrow budget",
                    liveness="idle")
        txt = "".join(t for t, _k in render._session_row(s, narrow=False, name_width=None))
        self.assertIn("…", txt)
        long_seg = max((t for t, k in render._session_row(s, narrow=False, name_width=None)
                        if k in ("name_idle", "name_work", "name_dim")), key=render._dw)
        self.assertLessEqual(render._dw(long_seg), render._TITLE_MAX)

    def test_dispatch_name_keeps_its_own_24_cell_compact_cap(self):
        """F-15's dispatch label cap is a separate axis — the session cap must not touch it."""
        self.assertEqual(render._TITLE_MAX, 24)
        long_slug = "a" * 80
        compact = render._compact_dispatch_name(long_slug)
        self.assertLessEqual(render._dw(compact), render._DISPATCH_NAME_MAX)

    def test_cjk_tail_cut_stays_display_cell_safe(self):
        """_clip_w must not split a 2-cell char or exceed the budget at the new cap."""
        cjk = "한글제목입니다" * 12
        for budget in (10, 11, 40, render._NAME_WIDE_MAX):
            out = render._clip_w(cjk, budget)
            self.assertLessEqual(render._dw(out), budget, "budget %d overflow" % budget)

    def test_name_zone_holds_a_capped_title_at_168(self):
        s = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="proj",
                    title="x" * 120, liveness="idle")
        nw = render._wide_name_width(168)
        segs = render._session_row(s, narrow=False, name_width=nw)
        name_seg = max((t for t, k in segs if k in ("name_idle", "name_work", "name_dim")),
                       key=render._dw)
        self.assertLessEqual(render._dw(name_seg), nw)
        self.assertLessEqual(render._dw(name_seg), render._NAME_WIDE_MAX)


class RowWidthRegressionTest(unittest.TestCase):
    """The cap's actual purpose: a wide row must stop growing with the terminal."""

    def _row_width(self, term_width, title):
        s = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="proj",
                    title=title, liveness="idle", ctx_pct=30, model="Fable 5",
                    effort="xhigh", elapsed_min=42, branch="main")
        segs = render._session_row(s, narrow=False,
                                   name_width=render._wide_name_width(term_width))
        return sum(render._dw(t) for t, _k in segs if t != render._RFLUSH)

    def test_long_title_row_does_not_grow_between_168_and_200(self):
        """Pre-v8 the name zone grew 77 → 109 across these widths, dragging the row with it."""
        long_title = "y" * 200
        self.assertEqual(self._row_width(168, long_title), self._row_width(200, long_title))

    def test_short_title_row_is_unaffected_by_the_cap(self):
        self.assertEqual(self._row_width(168, "short"), self._row_width(200, "short"))


if __name__ == "__main__":
    unittest.main()
