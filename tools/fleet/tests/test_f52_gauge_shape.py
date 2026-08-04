"""F-52a/b/c — thin gauge glyphs, window-proportional context track, liveness lead cell.

v36 (2026-08-04) replaced only F-51a's GLYPH and context-WIDTH clauses: the usage header meter
stays a fixed six cells, and every quantization / color / unknown-vs-0% rule is untouched.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render                                       # noqa: E402
from fleet.model import ContextProjection, DispatchJob, Session  # noqa: E402


FULL, EMPTY = render._BAR_FULL, render._BAR_EMPTY


def track_of(row):
    """The gauge track text of a context detail row (the two segments after the lead cell)."""
    return "".join(value for value, _key in row[0][2:4])


class F52aGlyphTest(unittest.TestCase):
    def test_gauge_glyphs_are_the_thin_mid_height_bars(self):
        self.assertEqual((FULL, EMPTY), ("━", "─"))

    def test_both_surfaces_still_share_one_producer(self):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                          rl_5h=75, rl_7d=30, mtime=1000)
        header = "".join(v for row in render._usage_header_rows([session]) for v, _k in row)
        detail = "".join(v for v, _k in render._context_detail_row(session)[0])
        self.assertIn(FULL, header)
        self.assertNotIn("█", header + detail)   # no battery block anywhere
        self.assertNotIn("░", header + detail)


class F52bTrackLengthTest(unittest.TestCase):
    def test_reference_windows_map_to_the_documented_track_lengths(self):
        cases = {1000000: 20, 256000: 5, 262144: 5, 200000: 4, 500000: 10, 2000000: 20}
        for window, cells in cases.items():
            with self.subTest(window=window):
                self.assertEqual(render._context_gauge_track(window), cells)

    def test_half_up_at_the_boundary_and_clamped_to_at_least_one_cell(self):
        # 20 * w / 1M == 2.5 exactly → half-up lands on 3, not banker's 2.
        self.assertEqual(render._context_gauge_track(125000), 3)
        for tiny in (1, 1000, 24999):
            self.assertEqual(render._context_gauge_track(tiny), 1)

    def test_unmeasured_window_falls_back_to_the_twenty_cell_baseline(self):
        for missing in (None, 0, -1, True, "1000000", float("nan"), float("inf")):
            with self.subTest(missing=missing):
                self.assertEqual(render._context_gauge_track(missing), render._CTX_TRACK_MAX)

    def _row(self, window, pct):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                          ctx_pct=pct, context_window_tokens=window)
        return render._context_detail_row(session, term_width=168)

    def test_row_track_follows_the_measured_window(self):
        self.assertEqual(len(track_of(self._row(1000000, 50))), 20)
        self.assertEqual(len(track_of(self._row(256000, 50))), 5)
        self.assertEqual(len(track_of(self._row(None, 50))), 20)   # unknown → baseline, row stays
        self.assertIn("50%", "".join(v for v, _k in self._row(None, 50)[0]))

    def test_no_depth_dependent_shrink_survives(self):
        """F-51a abolished the per-depth narrowing; length depends on the window only."""
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle", ctx_pct=50,
                          context_window_tokens=1000000)
        for depth in (0, 1, 2, 3):
            row = render._context_detail_row(session, depth=depth, term_width=200)
            self.assertEqual(len(track_of(row)), 20)

    def test_fill_is_half_up_over_the_track_with_reserved_ends(self):
        for pct, filled in ((None, 0), (0, 0), (1, 1), (2, 1), (3, 1), (50, 10),
                            (97, 19), (99, 19), (100, 20), (150, 20)):
            with self.subTest(pct=pct):
                segs = render._gauge_segs(pct, 99, track=20)
                self.assertEqual(sum(len(v) for v, _k in segs), 20)
                self.assertEqual(len(segs[0][0]), filled)

    def test_one_cell_track_never_over_reports(self):
        """A 1-cell track has no in-between cell — lighting it below 100% would read as full."""
        for pct in (None, 0, 1, 50, 99, 99.9):
            with self.subTest(pct=pct):
                self.assertEqual(render._gauge_segs(pct, 6, track=1)[0][0], "")
        self.assertEqual(render._gauge_segs(100, 6, track=1)[0][0], FULL)
        row = self._row(50000, 99)                      # 50K window → a single cell
        self.assertEqual(track_of(row), EMPTY)
        self.assertEqual(track_of(self._row(50000, 100)), FULL)

    def test_usage_header_meter_stays_six_cells_whatever_the_session_window(self):
        for window in (None, 256000, 1000000):
            with self.subTest(window=window):
                session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                                  rl_5h=75, rl_7d=30, mtime=1000,
                                  context_window_tokens=window)
                joined = "".join(v for row in render._usage_header_rows([session])
                                 for v, _k in row)
                self.assertIn("[" + FULL * 5 + EMPTY, joined)
                for chunk in joined.split("[")[1:]:
                    meter = chunk.split("]")[0]
                    self.assertEqual(len([c for c in meter if c in (FULL, EMPTY)]),
                                     render._GAUGE_W)

    def test_default_track_argument_is_the_usage_meter_width(self):
        self.assertEqual(render._gauge_segs(50, 99), render._gauge_segs(50, 99, track=6))


class F52cLivenessLeadTest(unittest.TestCase):
    def _lead(self, row):
        return row[0][1]

    def test_the_lead_cell_reuses_the_harness_row_glyph_and_color_key(self):
        for state in ("idle", "blocked", "unused", "degraded", "queued"):
            with self.subTest(state=state):
                session = Session(harness="claude", pid=1, cwd="/x", liveness=state,
                                  ctx_pct=40, slug="s", elapsed_min=1)
                glyph, key = render._glyph(state)
                text, row_key = self._lead(render._context_detail_row(session, term_width=168))
                self.assertEqual(text, glyph + " ")
                self.assertEqual(row_key, key)
                # …and it is literally the same key the harness row puts on its own glyph.
                self.assertIn(key, [k for _v, k in render._session_row(session, narrow=False)])

    def test_dispatch_rows_keep_the_dim_glyph_weight(self):
        """F-50f's plugin-queue job is the one dispatch row that owns a context window; it
        reuses this gauge row, so its lead mark must carry the DIM dispatch weight."""
        # `working` is the only state whose weight actually differs (g_spin vs g_spin_dim),
        # so it is the one that proves the dim flag reached the shared producer.
        job = DispatchJob(key="code", slug="w", harness="codex", depth=1, source="plugin-queue",
                          liveness="working", context=ContextProjection(40, "normal", "x"))
        row = render._dispatch_summary_detail_row(job, depth=1, term_width=168)
        self.assertEqual(self._lead(row)[1], render._glyph("working", dim=True)[1])
        self.assertNotEqual(render._glyph("working", dim=True)[1], render._glyph("working")[1])

    def test_no_book_icon_and_no_new_state_vocabulary(self):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle", ctx_pct=40)
        visible = "".join(v for v, _k in render._context_detail_row(session)[0])
        self.assertNotIn("\U0001f4da", visible)
        self.assertFalse(hasattr(render, "_CTX_LABEL"))
        keys = {k for _v, k in render._context_detail_row(session)[0]}
        self.assertTrue(keys <= set(render._GLYPH_KEY.values()) | {None, "dim", "lvl_g",
                                                                  "lvl_y", "lvl_r", "g_spin"})

    def test_label_ledger_matches_the_real_display_cells(self):
        """`_CTX_LABEL_W` is hardcoded (module load runs before `_dw` exists) — pin it against
        the actual width of every glyph the lead cell can ever hold."""
        glyphs = set(render._LIVE_GLYPH.values()) | set(render._SPIN)
        for glyph in glyphs:
            with self.subTest(glyph=glyph):
                self.assertEqual(render._dw(glyph + " "), render._CTX_LABEL_W)


class F52WidthLedgerTest(unittest.TestCase):
    def test_left_anchor_and_wide_slack_ledger_are_untouched(self):
        self.assertEqual(render._CONTEXT_INDENT_W, 4)
        self.assertEqual(render._CTX_W, 24)
        # F-54 (_HMW 33→38→42) charges 9 more cells to `fixed_row` than the v35 ledger, so every
        # slack entry drops by exactly that much and the alloc ladder shifts right by the same
        # number of widths. What this test guards — the left anchor (_CONTEXT_INDENT_W) and the
        # gauge base (_CTX_W) asserted above, plus the boost-first/name-to-cap/remainder-to-gauge
        # priority — is untouched: 120 still sits at the (_NW_S, _CTX_W) floor, and 400 is still
        # name-capped with all remaining slack in the gauge. The v40 +4 pushed the cap's first
        # width 172→176, so 168 dropped one more step (32, was 36 at _HMW=38).
        self.assertEqual([render._wide_slack(w) for w in (60, 120, 168, 200, 400)],
                         [-64, -4, 44, 76, 276])
        self.assertEqual([render._wide_alloc(w) for w in (120, 168, 400)],
                         [(28, 24), (32, 36), (40, 260)])

    def test_row_starts_at_the_harness_name_column_and_fits_every_layout(self):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle", ctx_pct=63,
                          context_window_tokens=1000000, summary="NOW")
        for width in (168, 138, 120, 100, 60):
            with self.subTest(width=width):
                visible = "".join(v for v, _k in
                                  render._context_detail_row(session, term_width=width)[0])
                self.assertLessEqual(render._dw(visible), width)
                self.assertEqual(render._dw(visible[:visible.index(render._LIVE_GLYPH["idle"])]),
                                 render._CONTEXT_INDENT_W)
                self.assertEqual(render._dw(visible[:visible.index("NOW")]), render._NAME_COL)

    def test_legend_gained_no_new_entry(self):
        """F-12(c): the lead cell is a STATE mark, already covered by the state legend — the
        legend line (last rendered row) gains no gauge item of its own."""
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle", ctx_pct=63,
                          slug="s", elapsed_min=1)
        lines = render._build_lines([session], [], "fleet", False, 0,
                                    layout="wide", term_width=168)
        legend = "".join(v for v, _k in [ln for ln in lines if ln][-1])
        self.assertIn("idle", legend)
        self.assertNotIn("context", legend)
        self.assertNotIn(FULL, legend)
        self.assertNotIn(EMPTY, legend)


if __name__ == "__main__":
    unittest.main()
