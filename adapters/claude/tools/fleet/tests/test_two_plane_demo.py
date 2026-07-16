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
        # grammar #2 — pure indent, no connector of its own (no tree lattice ever reached here).
        text = _joined(self._lines(120))
        self.assertIn("⚡ Explore", text)
        self.assertIn("● 2m51s", text)
        self.assertIn("✓ 4m04s", text)

    def test_dispatch_rows_use_the_spawn_arrow_and_capability_glyph(self):
        # grammar #3, round-2 — the ├─/└─ tree lattice is retired in favor of the session-child
        # ↳ spawn arrow (matches render.py's own real dispatch-row convention), 🔧 capability
        # glyph, job-contract parenthetical.
        text = _joined(self._lines(120))
        self.assertIn("▸ claude code", text); self.assertIn("↳ ", text)
        self.assertIn("▸ codex", text)
        self.assertIn("code (dev·thr·owner)", text)
        self.assertIn("(dev·thr·owner)", text)
        self.assertIn("(dev·quick·quick_owner)", text)
        # r10 — model is FIRST-CLASS on spawned rows, same _model_cell idiom as the grid
        self.assertIn("Opus 4.8 (high)", text)
        self.assertIn("gpt-5.5 (medium)", text)
        self.assertIn("haiku (medium)", text)
        self.assertIn("sonnet (medium)", text)
        # r3 — qa retired as a separate axis (CONVENTIONS §1.1): no derived-qa token anywhere.
        self.assertNotIn("~thorough", text)
        # r3 — mode restored (parity) and the slug marked as a branch/worktree name.
        self.assertNotIn("code (dev) ", text)
        self.assertIn("⎇ usage-accuracy", text)
        self.assertIn("⎇ rate-window", text)

    def test_no_tree_lattice_survives_in_this_view(self):
        # round-2 (user-confirmed) — the vertical spine and rail connectors are fully retired;
        # only the ↳ spawn arrow and the canvas's own `└ exec:B` worker sub-row remain.
        text = _joined(self._lines(120))
        self.assertNotIn("│", text)
        self.assertNotIn("├─", text)
        self.assertNotIn("└─", text)

    def test_subagents_render_as_one_horizontal_strip(self):
        # r7 (user) — sub-agents collapse to ONE horizontal strip per parent: type only
        # (one-two words) + status glyph + elapsed, ` · ` separated; descriptions moved off
        # the board (they remain collector data for a detail surface).
        lines = self._lines(120)
        text = _joined(lines)
        self.assertIn("⚡ Explore ● 2m51s · Explore ✓ 4m04s", text)
        self.assertIn("⚡ 개발팀 ● 1m12s", text)
        self.assertIn("⚡ Explore ✓ 48s", text)
        # no per-agent quoted description rows remain
        self.assertNotIn("제목 파이프라인 조사", text)
        self.assertNotIn("파서 구현", text)

    def test_dispatch_rows_sit_tight_against_their_session(self):
        # r7 (user: "분사 세션은 메인 세션이랑 여백을 없애고") + the engine's own "rows stay
        # tight" rule — no blank separator rows between a session block and its ↳ rows.
        lines = two_plane.build_lines(120, "wide")
        def txt(ln):
            return "".join(t for t, _k in ln if not render._is_fill(t)) if ln else ""
        for i, ln in enumerate(lines):
            if "↳" in txt(ln):
                self.assertTrue(txt(lines[i - 1]).strip(),
                                "blank row directly above a ↳ row at %d" % i)

    def test_canvas_breadcrumb_uses_the_existing_separator(self):
        # grammar #4 — stage canvas below the conductor, joined by the existing ' › ' breadcrumb.
        # r4: the canvas is the conductor's SUMMARY only (SD-F2) — worker facts live on the
        # depth-2 rail rows below, so the active node carries no (harness·model·effort) meta.
        text = _joined(self._lines(120))
        self.assertIn("plan ✓12m › exec ● 8m", text)
        self.assertIn("› test › report", text)
        self.assertNotIn("test ○", text)

    def test_depth2_stage_workers_are_rail_rows_not_fused_nodes(self):
        # r4 (user-confirmed) — a depth-2 stage worker is an ENTITY, so it gets the existing
        # fleet grammar: a spawn arrow one level deeper than its conductor, with the SD-F1
        # human stage label + ⎇ slug identity, bootstrap type, and its own worker facts.
        lines = self._lines(120)
        text = _joined(lines)
        self.assertIn("⎇ usage-accuracy", text)
        self.assertIn("exec:B (stage)", text)
        self.assertIn("exec (stage)", text)
        self.assertIn("exec:B (stage)", text)
        # positional attribution replaced the @<node> tag entirely
        self.assertNotIn("@exec", text)
        # the depth-2 arrow is strictly deeper than the depth-1 arrow
        def arrow_col(snippet):
            for ln in lines:
                if ln and snippet in "".join(t for t, _k in ln):
                    s = "".join(t for t, _k in ln)
                    return s.index("↳")
            self.fail("row containing %r not found" % snippet)
        self.assertGreater(arrow_col("exec (stage)"), arrow_col("code (dev·thr·owner)"))

    def test_mem_events_are_scoped_under_their_own_group(self):
        # grammar #6 — per-repo mem events, not a board-wide dump.
        text = _joined(self._lines(120))
        self.assertIn("durable/project", text)
        self.assertIn("working/expired", text)

    def test_mem_zone_sits_below_a_subtle_in_band_divider(self):
        # r5 (user) — a dim rule ON the tint separates the card's mem zone from its rows;
        # it lives inside the band (tint sentinel present) and directly precedes the first
        # mem event row.
        lines = two_plane.build_lines(120, "wide")
        idx_rule = idx_mem = None
        for i, ln in enumerate(lines):
            if not ln:
                continue
            s = "".join(t for t, _k in ln if not render._is_fill(t))
            if idx_rule is None and s.strip() and set(s.strip()) == {"─"}:
                self.assertEqual(ln[0][0], render._TINT_BODY_HOT)   # on the band, not chrome
                idx_rule = i
            if idx_mem is None and "14:02" in s:
                idx_mem = i
        self.assertIsNotNone(idx_rule)
        self.assertIsNotNone(idx_mem)
        self.assertEqual(idx_mem, idx_rule + 1)

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

    def test_card_tint_is_continuous(self):
        """r3 (user: "분사 세션을 틴트로 갈라버리면 어쩌냐") — every row INSIDE a group card,
        including blank separators, carries that card's tint sentinel; an untinted blank
        would split the card's band into visual fragments. Only between-card gaps are None."""
        lines = two_plane.build_lines(168, "wide")
        def tint_of(ln):
            if not ln:
                return None
            t = ln[0][0]
            return t if t in (render._TINT_BODY_HOT, render._TINT_BODY) else None
        # walk each card: from its first tinted row to its last, no None and no tint change
        i = 0
        cards = 0
        while i < len(lines):
            t = tint_of(lines[i])
            if t is None:
                i += 1
                continue
            j = i
            last = i
            while j < len(lines) and tint_of(lines[j]) == t:
                last = j
                j += 1
            for k in range(i, last + 1):
                self.assertEqual(tint_of(lines[k]), t,
                                 "card tint broken at line %d" % k)
            cards += 1
            i = j
        self.assertEqual(cards, 2)   # agent_setting (hot) + worklog-board (body)


class BoldScopeTest(unittest.TestCase):
    """round-2 (user-confirmed) — bold is reserved for the main-session row (`_ROW_BOLD`)
    alone. Every other bold source this view used to carry (canvas active node, dispatch
    ▸/🔧, group header name+glyph) now resolves to a plain (non-bold, non-dim) engine color
    key instead of the bold one — checked at the color_key level, since these tests run
    headless (no curses attrs to inspect)."""

    def _line_containing(self, lines, snippet):
        for ln in lines:
            if not ln:
                continue
            if any(snippet in t for t, _k in ln):
                return ln
        self.fail("no row contains %r" % snippet)

    def test_canvas_active_node_uses_a_plain_stage_hue_not_the_bold_engine_one(self):
        lines = two_plane.build_lines(120, "wide")
        ln = self._line_containing(lines, "exec ● 8m")
        keys = [k for _t, k in ln]
        self.assertNotIn("stg1_on", keys)
        self.assertIn("fam_opus", keys)

    def test_dispatch_rows_use_plain_stage_hues_not_bold_ones(self):
        lines = two_plane.build_lines(120, "wide")
        keys = set()
        for snippet in ("usage-accuracy", "rate-window"):
            keys.update(k for _t, k in self._line_containing(lines, snippet))
        self.assertNotIn("stg0_on", keys)
        self.assertNotIn("stg1_on", keys)
        self.assertIn("fam_opus", keys)   # usage-accuracy (cyan, was stg1_on)
        self.assertIn("eff_high", keys)   # rate-window (blue, was stg0_on)

    def test_group_header_name_and_glyph_drop_bold_but_keep_hue(self):
        lines = two_plane.build_lines(120, "wide")
        active = self._line_containing(lines, "agent_setting")
        active_key = dict(active)["agent_setting"]
        self.assertEqual(active_key, "grp_live")           # was "grp_hot" (bold green)
        self.assertNotIn("g_work", [k for _t, k in active])  # blink-on frame no longer bold

        cold = self._line_containing(lines, "worklog-board")
        cold_key = dict(cold)["worklog-board"]
        self.assertIsNone(cold_key)                        # was "grp" (bold, no hue)


if __name__ == "__main__":
    unittest.main()
