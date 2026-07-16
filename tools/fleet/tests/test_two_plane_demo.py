#!/usr/bin/env python3
"""Hermetic unit tests — two-plane provisional-grammar demo (`--demo two-plane`, additive).

Zero-regression contract: `--demo two-plane` is the ONLY entry point into this code path
(fleet.py's `--demo` nargs='?' const=True keeps bare `--demo` unchanged); `render._build_lines`
must behave byte-for-byte as before whenever `_TWO_PLANE_DEMO` stays False (the default).
"""
import os
import sys
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import render                    # noqa: E402
from fleet import two_plane                 # noqa: E402
from fleet import fleet as fleet_cli        # noqa: E402


def _joined(lines):
    return "\n".join("".join(t for t, _k in ln) for ln in lines if ln)


class ArgParseTest(unittest.TestCase):
    def test_bare_demo_flag_is_still_a_plain_true(self):
        self.assertIs(fleet_cli.parse_args([]).demo, False)
        self.assertIs(fleet_cli.parse_args(["--demo"]).demo, True)

    def test_demo_two_plane_mode_is_the_literal_string(self):
        self.assertEqual(fleet_cli.parse_args(["--demo", "two-plane"]).demo, "two-plane")

    def test_demo_flag_does_not_swallow_a_following_option(self):
        args = fleet_cli.parse_args(["--demo", "--once"])
        self.assertIs(args.demo, True)
        self.assertTrue(args.once)


class DefaultPathUnchangedTest(unittest.TestCase):
    """The flag defaults False — every existing call site is untouched unless a test
    explicitly opts in, and every test undoes the toggle in tearDown (module-global state)."""

    def tearDown(self):
        render.set_two_plane_demo(False)

    def test_flag_defaults_false(self):
        self.assertFalse(render._TWO_PLANE_DEMO)

    def test_normal_build_lines_ignores_two_plane_module_when_flag_is_false(self):
        lines = render._build_lines([], [], "both", narrow=False, malformed=0,
                                    layout="wide", memory=None, term_width=120)
        text = _joined(lines)
        self.assertNotIn("two-plane demo", text)
        self.assertNotIn("agent_setting", text)

    def test_setting_flag_true_then_false_restores_normal_output(self):
        before = _joined(render._build_lines([], [], "both", narrow=False, malformed=0,
                                              layout="wide", memory=None, term_width=120))
        render.set_two_plane_demo(True)
        render.set_two_plane_demo(False)
        after = _joined(render._build_lines([], [], "both", narrow=False, malformed=0,
                                            layout="wide", memory=None, term_width=120))
        self.assertEqual(before, after)


class TwoPlaneGrammarTest(unittest.TestCase):
    def tearDown(self):
        render.set_two_plane_demo(False)

    def _lines(self, term_width):
        render.set_two_plane_demo(True)
        layout = render._layout_mode(term_width)
        return render._build_lines([], [], "both", narrow=(term_width < render._NARROW_CUTOFF),
                                   malformed=0, layout=layout, memory=None, term_width=term_width)

    def test_renders_at_60_120_168_with_no_exception(self):
        for w in (60, 120, 168):
            lines = self._lines(w)
            self.assertTrue(lines)

    def test_grid_plane_reuses_the_real_session_row_bold_marker(self):
        # grammar #1/#8 — main session rows are the existing grid, entirely bold (_ROW_BOLD).
        lines = self._lines(120)
        bold_rows = [ln for ln in lines
                    if ln and any(seg[0] == render._ROW_BOLD for seg in ln[:2])]
        self.assertGreaterEqual(len(bold_rows), 3)   # 3 fixture sessions

    def test_no_subagent_count_badge_on_the_session_row(self):
        # grammar #2 — ⚡N suffix must NOT appear on the grid row (the ⚡ rows below it already
        # show the same information; a badge would be a duplicate).
        text = _joined(self._lines(120))
        self.assertNotIn("⚡1", text)
        self.assertNotIn("⚡2", text)

    def test_subagent_rows_use_no_connector_and_show_status_glyph(self):
        # grammar #2 — inset next to the spine, no ├─/└─ connector of their own.
        text = _joined(self._lines(120))
        self.assertIn("⚡ Explore", text)
        self.assertIn("● 2m51s", text)
        self.assertIn("✓ 4m04s", text)

    def test_dispatch_rows_use_rail_connectors_and_capability_glyph(self):
        # grammar #3 — ├─▸ / └─▸ rail connectors, 🔧 capability glyph, job-contract parenthetical.
        text = _joined(self._lines(120))
        self.assertIn("├─▸", text)
        self.assertIn("└─▸", text)
        self.assertIn("🔧 code", text)
        self.assertIn("(thr · ~thorough)", text)
        self.assertIn("(quick · gpt·med)", text)

    def test_canvas_breadcrumb_uses_the_existing_separator(self):
        # grammar #4 — stage canvas below the conductor, joined by the existing ' › ' breadcrumb.
        text = _joined(self._lines(120))
        self.assertIn("plan ✓12m › exec ● 8m", text)
        self.assertIn("test ○ › report ○", text)
        self.assertIn("exec:B ● 3m", text)

    def test_node_anchored_subagents_carry_an_at_tag(self):
        # grammar #5 — depth-2 worker sub-agents tagged back to their canvas node.
        text = _joined(self._lines(120))
        self.assertIn("@exec", text)
        self.assertIn("@exec:B", text)

    def test_mem_events_are_scoped_under_their_own_group(self):
        # grammar #6 — per-repo mem events, not a board-wide dump.
        text = _joined(self._lines(120))
        self.assertIn("durable/project", text)
        self.assertIn("working/expired", text)

    def test_branch_cell_carries_the_new_glyph(self):
        # grammar #7 — ⎇ glyph is new to THIS view only (asserted separately below).
        text = _joined(self._lines(120))
        self.assertIn("⎇ main", text)
        self.assertIn("⎇ wt-usage", text)

    def test_loop_job_renders_as_a_project_level_plane_row(self):
        # grammar #9 — a parent-less loop job is its own ▸ row, `loop:<name> queued · next <t>`.
        text = _joined(self._lines(120))
        self.assertIn("loop:note", text)
        self.assertIn("queued · next 18m", text)

    def test_branch_glyph_is_scoped_to_two_plane_only(self):
        # grammar #7 — bare _branch_seg (used by every other view) must stay unmodified.
        seg = render._branch_seg("/tmp/x", "main", dim=False)
        self.assertNotIn("⎇", seg[0])


class BuildLinesModuleTest(unittest.TestCase):
    """Direct unit coverage of `two_plane.build_lines`, independent of the render.py hook."""

    def test_returns_a_list_of_line_or_none(self):
        lines = two_plane.build_lines(120, "wide")
        self.assertIsInstance(lines, list)
        for ln in lines:
            self.assertTrue(ln is None or isinstance(ln, list))

    def test_pulse_row_reflects_the_real_fixture_counts(self):
        sessions, jobs = two_plane._fixture()
        pulse_text = "".join(t for t, _k in render._pulse_segs(sessions, jobs))
        n_working = sum(1 for s in sessions if s.liveness == "working")
        self.assertIn("%d working" % n_working, pulse_text)


if __name__ == "__main__":
    unittest.main()
