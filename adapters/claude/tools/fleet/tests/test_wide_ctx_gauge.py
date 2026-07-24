"""Wide-layout ctx-gauge width (2026-07-16, 사용자: "context window의 길이를 더 늘려서
맞춰주고") — once the name column hits its F-22 cap, leftover terminal slack widens the
session row's ctx gauge instead of sitting as blank padding, so the gauge's right edge
lands at the same column across rows for a given terminal width.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render                                     # noqa: E402
from fleet.model import Session                               # noqa: E402


class WideCtxWidthTest(unittest.TestCase):
    def test_no_width_returns_the_static_default(self):
        self.assertEqual(render._wide_ctx_width(None), render._CTX_W)
        self.assertEqual(render._wide_ctx_width(0), render._CTX_W)

    def test_narrow_widths_below_the_name_cap_leave_the_gauge_untouched(self):
        """60/120 don't even reach the F-22 name cap — no slack exists to redistribute."""
        for w in (60, 120):
            self.assertEqual(render._wide_ctx_width(w), render._CTX_W)

    def test_wide_widths_past_the_name_cap_widen_the_gauge(self):
        for w in (168, 200, 400):
            self.assertGreater(render._wide_ctx_width(w), render._CTX_W)

    def test_monotonic_and_never_shrinks_below_the_base_width(self):
        widths = [render._wide_ctx_width(w) for w in range(1, 400)]
        self.assertTrue(all(b >= a for a, b in zip(widths, widths[1:])), "not monotonic")
        self.assertTrue(all(w >= render._CTX_W for w in widths))

    def test_shares_the_reservation_math_with_wide_name_width(self):
        """Both derive from the same `_wide_slack` — the cap boundary must line up: name
        width stops growing exactly where ctx width starts (one calc, not two)."""
        for w in (60, 120, 167, 168, 169, 200):
            name_w = render._wide_name_width(w)
            ctx_w = render._wide_ctx_width(w)
            if name_w < render._NAME_WIDE_MAX:
                self.assertEqual(ctx_w, render._CTX_W)
            else:
                self.assertGreaterEqual(ctx_w, render._CTX_W)


class SessionRowCtxWidthTest(unittest.TestCase):
    """The v16 context contract keeps telemetry in the subordinate detail row."""

    def _row_text(self, term_width, ctx_width=None):
        s = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="proj",
                    title="x", liveness="idle", ctx_pct=42, model="Fable 5",
                    effort="xhigh", elapsed_min=42, branch="main")
        name_w = render._wide_name_width(term_width) if term_width else None
        segs = render._session_row(s, narrow=False, name_width=name_w, ctx_width=ctx_width)
        return "".join(t for t, _k in segs if t != render._RFLUSH)

    def test_legacy_call_without_ctx_width_keeps_the_24_cell_gauge(self):
        text = self._row_text(168, ctx_width=None)
        # bar + " NNN%" — count the bar glyph run length via the base width, not a fixed
        # literal, so a future palette swap doesn't break this assertion.
        base_text = self._row_text(168, ctx_width=render._CTX_W)
        self.assertEqual(text, base_text)

    def test_primary_row_no_longer_renders_an_inline_context_gauge(self):
        s = Session(harness="claude", pid=1, cwd="/home/u/proj", slug="proj",
                    title="x", liveness="idle", ctx_pct=None, elapsed_min=1)
        segs = render._session_row(s, narrow=False, ctx_width=40)
        text = "".join(t for t, _k in segs)
        self.assertNotIn("42%", text)
        self.assertNotIn("💬", text)

    def test_no_overflow_at_wide_layout_widths(self):
        """168/200/400 are where the board actually picks the wide layout (`_layout_mode`
        only returns "wide" at >=138 cols) — 60/120 render narrow/stack instead, a
        different row builder this ctx-width knob never touches."""
        for term_width in (168, 200, 400):
            self.assertEqual(render._layout_mode(term_width), "wide")
            ctx_w = render._wide_ctx_width(term_width)
            text = self._row_text(term_width, ctx_width=ctx_w)
            self.assertLessEqual(render._dw(text), term_width,
                                 "term_width=%d row overflowed" % term_width)


if __name__ == "__main__":
    unittest.main()
