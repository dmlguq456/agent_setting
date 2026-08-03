import unittest
import os
import sys
import json
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render
from fleet.model import ContextProjection, Session


class F51GaugeTest(unittest.TestCase):
    def test_fixed_width_and_half_up(self):
        self.assertEqual("".join(x[0] for x in render._gauge_segs(75, 99)), "█████░")
        for pct in (None, 0, -1):
            self.assertEqual("".join(x[0] for x in render._gauge_segs(pct, 1)), "░░░░░░")
        self.assertEqual("".join(x[0] for x in render._gauge_segs(100, 1)), "██████")

    def test_acceptance_quantization_table_and_pct_boundaries(self):
        expected = {None: 0, 0: 0, 1: 1, 8: 1, 16: 1, 50: 3,
                    75: 5, 84: 5, 92: 5, 99: 5, 100: 6, 150: 6}
        for pct, filled in expected.items():
            with self.subTest(pct=pct):
                segs = render._gauge_segs(pct, 6)
                self.assertEqual(sum(len(value) for value, _key in segs), 6)
                self.assertEqual(sum(len(value) for value, _key in segs
                                     if "█" in value), filled)
        self.assertEqual(render._pct_key(50), render._pct_key(50.0))
        self.assertEqual(render._pct_key(80), render._pct_key(80.0))

    def test_width_shim_is_constant(self):
        self.assertEqual({render._compact_context_gauge_width(w, depth=d)
                          for w in (20, 40, 60, 100, 138, 168, 200, 400)
                          for d in (0, 1, 2)}, {6})

    def test_unknown_and_zero_values_are_distinct(self):
        text = lambda pct: "".join(x[0] for x in render._context_detail_row(
            type("E", (), {"liveness": "working", "ctx_pct": pct, "summary": None})())[0])
        self.assertIn("—", text(None))
        self.assertIn("0%", text(0))

    def test_context_now_anchor_and_widths(self):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="working",
                          context=ContextProjection(50, "normal", "x"), summary="NOW",
                          rl_5h=50, rl_7d=50)
        for width, layout in ((168, "wide"), (138, "wide"), (100, "narrow"),
                              (60, "stack")):
            with self.subTest(width=width, layout=layout):
                row = render._context_detail_row(session, term_width=width)
                visible = "".join(value for value, _key in row[0])
                self.assertEqual(render._dw(visible[:visible.index("NOW")]), render._NAME_COL)
                self.assertLessEqual(render._dw(visible), width)
                headers = render._usage_header_rows([session], layout=layout)
                if headers:
                    self.assertTrue(any("█" in value or "░" in value or "·" in value
                                        for value, _key in headers[0]))

    def test_header_row_fits_and_never_grew_past_the_old_wider_gauge(self):
        """A3: five fixtures — wide@168/wide@138/narrow@100/stack@60, plus a plain (--once)
        call with no term_width at all. Every row must fit its terminal, and the row's total
        length must never exceed what the OLD (pre-F51) 8/12-cell gauge contract would have
        produced — the new fixed six-cell battery (`_GAUGE_W`) is strictly narrower, so
        substituting the old width in place of `_GAUGE_W` can only grow the row, never shrink
        it, which is exactly the non-increase invariant this test locks in."""
        old_gauge_w = 12
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                          rl_5h=92, rl_7d=30, mtime=1000)
        fixtures = [(168, "wide"), (138, "wide"), (100, "narrow"), (60, "stack")]
        for term_width, layout in fixtures:
            with self.subTest(term_width=term_width, layout=layout):
                rows = render._usage_header_rows([session], layout=layout)
                self.assertTrue(rows)
                for row in rows:
                    text = "".join(v for v, _k in row)
                    new_len = render._dw(text)
                    self.assertLessEqual(new_len, term_width)
                    num_gauges = text.count("[")
                    old_len = new_len + num_gauges * (old_gauge_w - render._GAUGE_W)
                    self.assertLessEqual(new_len, old_len)
        # plain (--once) path: no term_width constraint, but the same fixed six-cell gauge
        # applies unconditionally.
        plain_rows = render._usage_header_rows([session])
        self.assertTrue(plain_rows)
        joined = "".join(v for row in plain_rows for v, _k in row)
        self.assertIn("[" + render._BAR_FULL * 5 + render._BAR_EMPTY, joined)

    def test_stale_window_keeps_dotted_track_but_preserves_fill_and_pct_colors(self):
        """A5: a stale usage window shows an empty `·` track while the fill segment and the
        percent number both keep their `_pct_key` color (92% stays lvl_r, 30% stays lvl_g) —
        stale means "don't trust the freshness", not "hide the level"."""
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                          rl_5h=92, rl_7d=30, mtime=1000)
        session._usage_freshness = "stale"
        row = render._usage_header_rows([session], layout="wide")[0]
        visible = "".join(v for v, _k in row)
        self.assertTrue(all(len(track) == render._GAUGE_W
                            for track in re.findall(r"[█·]+", visible)))
        fill_keys = {k for v, k in row if render._BAR_FULL in v}
        self.assertIn("lvl_r", fill_keys)
        self.assertIn("lvl_g", fill_keys)
        dotted_tracks = [v for v, k in row if k == "dim" and v and set(v) == {"·"}]
        self.assertTrue(dotted_tracks)
        self.assertEqual(sorted(map(len, dotted_tracks)), [1, 4])
        pct_keys = {k for v, k in row if "%" in v}
        self.assertIn("lvl_r", pct_keys)
        self.assertIn("lvl_g", pct_keys)

    def test_unknown_window_is_dotted_track_and_em_dash(self):
        """A5: an unknown usage window (no cached value at all) shows `·`×6 track plus a bare
        `—`, distinct from both the stale window above and the 0% filled-track case."""
        session = Session(harness="claude", pid=1, cwd="/x", liveness="idle",
                          rl_5h=None, rl_7d=None, mtime=1000)
        session._usage_freshness = "unknown"
        row = render._usage_header_rows([session], layout="wide")[0]
        joined = "".join(v for v, _k in row)
        self.assertIn("·" * render._GAUGE_W, joined)
        self.assertIn("—", joined)
        self.assertNotIn(render._BAR_FULL, joined)

    def test_wide_alloc_matches_the_frozen_ledger_fixture_exactly(self):
        """A8: `f51_wide_ledger_v35.json` records `_wide_slack`/`_wide_name_width`/
        `_wide_ctx_width` for every terminal width 60..400 — recompute all three and diff
        against the frozen ledger so a future edit to the wide slack ladder cannot silently
        regress without this fixture failing."""
        path = os.path.join(os.path.dirname(__file__), "fixtures", "f51_wide_ledger_v35.json")
        with open(path, encoding="utf-8") as fh:
            ledger = json.load(fh)
        self.assertEqual(len(ledger), 341)
        for w in range(60, 401):
            expected = ledger[str(w)]
            name_w, ctx_w = render._wide_alloc(w)
            slack = render._wide_slack(w)
            with self.subTest(w=w):
                self.assertEqual(name_w, expected["wide_name_width"])
                self.assertEqual(ctx_w, expected["wide_ctx_width"])
                self.assertEqual(slack, expected["wide_slack"])

    def test_gauge_surfaces_never_emit_tilde(self):
        session = Session(harness="claude", pid=1, cwd="/x", liveness="working",
                          ctx_pct=50, summary="NOW", branch="main")
        surfaces = [render._gauge_segs(50, 99),
                    render._context_detail_row(session),
                    render._usage_header_rows([session]),
                    render._branch_suffix_segs("/tmp", "main")]
        for surface in surfaces:
            with self.subTest(surface=surface):
                self.assertNotIn("~", repr(surface))


if __name__ == "__main__":
    unittest.main()
