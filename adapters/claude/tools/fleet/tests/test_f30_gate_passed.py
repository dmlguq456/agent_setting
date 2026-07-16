#!/usr/bin/env python3
"""Hermetic unit tests — completion-gate PASS evidence (prd.md:308, v10 minor #2).

The v10 cycle left `gate_passed` as an honest gap: no completion marker existed anywhere on
disk (`plans/2026-07-15_fleet-v10-process-view/_internal/carryover.md` §1). stage-dispatch v13
(SD-56) landed the first real ones, so `fixtures/completion/rt-5fd84b9bcf8a799c/` is a VERBATIM
copy of that route's four markers, paired with `fixtures/route/real_sd13_staged.json` — the
actual record they were written against. Every mismatch/garbage case is derived from those
reals inside a tempdir, so the pass path is proven against production bytes and the no-claim
paths are proven against minimal, explainable mutations of them.

Contract under test (prd.md:308): marker present AND route_id/route_hash both match the record
= passed (True). EVERYTHING else — absent, route_id mismatch, hash mismatch, garbage json,
unreadable dir — is `None` ("무주장"), never False and never a failure glyph.

Stdlib unittest only; tempfile.TemporaryDirectory + mock (test_f28_route.py precedent). No
writes to the live `.dispatch/completion/` tree.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import route                     # noqa: E402
from fleet import render                    # noqa: E402

_FIXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
_ROUTE_FIX = os.path.join(_FIXDIR, "route", "real_sd13_staged.json")
_MARKER_FIX = os.path.join(_FIXDIR, "completion", "rt-5fd84b9bcf8a799c")

_NODES = ("plan", "execute", "test", "report")


class GateMarkBase(unittest.TestCase):
    """Builds a throwaway agent-home whose `.dispatch/completion/<route_id>/` holds copies of
    the real markers. `self.home` is what `gate_mark(home=...)` / `AGENT_HOME` point at."""

    def setUp(self):
        route.clear_cache()
        self.record = route.load(_ROUTE_FIX)
        self.assertIsNotNone(self.record, "real SD-13 record fixture must load")
        self.route_id = self.record["route_id"]
        self._tmp = tempfile.TemporaryDirectory()
        self.home = self._tmp.name
        self.cdir = os.path.join(self.home, ".dispatch", "completion", self.route_id)
        os.makedirs(self.cdir)
        for node in _NODES:
            shutil.copy(os.path.join(_MARKER_FIX, node + ".json"),
                        os.path.join(self.cdir, node + ".json"))

    def tearDown(self):
        self._tmp.cleanup()
        route.clear_cache()

    def _write(self, name, payload):
        path = os.path.join(self.cdir, name)
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(payload, str):
                f.write(payload)
            else:
                json.dump(payload, f)
        route.clear_cache()   # the cache is mtime+size keyed; same-second rewrites can collide
        return path

    def _marker(self, node):
        with open(os.path.join(_MARKER_FIX, node + ".json"), encoding="utf-8") as f:
            return json.load(f)


class GateMarkTest(GateMarkBase):
    def test_real_markers_all_pass(self):
        """The whole point: the repo's first four production markers read as PASSED against the
        record they were actually written from."""
        for node in _NODES:
            with self.subTest(node=node):
                self.assertIs(route.gate_mark(self.record, node, home=self.home), True)

    def test_absent_marker_is_no_claim(self):
        os.remove(os.path.join(self.cdir, "test.json"))
        route.clear_cache()
        self.assertIsNone(route.gate_mark(self.record, "test", home=self.home))
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)

    def test_absent_route_dir_is_no_claim(self):
        shutil.rmtree(self.cdir)
        route.clear_cache()
        for node in _NODES:
            self.assertIsNone(route.gate_mark(self.record, node, home=self.home))

    def test_route_id_mismatch_is_no_claim_not_failure(self):
        m = self._marker("plan")
        m["route_id"] = "rt-0000000000000000"
        self._write("plan.json", m)
        # `None`, not False — a marker we cannot tie to this record is silence, not a verdict.
        self.assertIsNone(route.gate_mark(self.record, "plan", home=self.home))

    def test_route_hash_mismatch_is_no_claim(self):
        m = self._marker("plan")
        m["route_hash"] = "sha256:" + ("0" * 64)
        self._write("plan.json", m)
        self.assertIsNone(route.gate_mark(self.record, "plan", home=self.home))

    def test_garbage_json_never_raises(self):
        for junk in ("{not json at all", "", "[]", "null", '"a string"', "\x00\xff"):
            with self.subTest(junk=junk):
                self._write("plan.json", junk)
                self.assertIsNone(route.gate_mark(self.record, "plan", home=self.home))

    def test_marker_missing_required_fields_is_no_claim(self):
        for drop in ("route_id", "route_hash"):
            with self.subTest(drop=drop):
                m = self._marker("plan")
                del m[drop]
                self._write("plan.json", m)
                self.assertIsNone(route.gate_mark(self.record, "plan", home=self.home))

    def test_optional_writer_fields_are_not_required(self):
        """The real markers carry NO `sequence`/`completed_at`/`schema_version` even though
        capability-route.py's writer sets the first two — requiring them would reject production
        evidence. Adding them must not break the read either."""
        m = self._marker("plan")
        self.assertNotIn("sequence", m)
        self.assertNotIn("schema_version", m)
        m["sequence"] = 3
        m["completed_at"] = "2026-07-16T09:53:00Z"
        self._write("plan.json", m)
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)

    def test_canonical_outranks_stale_history(self):
        """History files exist alongside canonical; canonical is what the writer atomically
        replaces with the newest, so a stale mismatching history file must not demote it."""
        stale = self._marker("plan")
        stale["route_hash"] = "sha256:" + ("0" * 64)
        self._write("plan.1.json", stale)
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)

    def test_history_latest_wins_when_canonical_absent(self):
        """Torn window (history written, canonical replace not yet done): the highest sequence
        is the latest, and a lower-sequence stale marker must not win."""
        good = self._marker("plan")
        stale = dict(good, route_hash="sha256:" + ("0" * 64))
        os.remove(os.path.join(self.cdir, "plan.json"))
        self._write("plan.1.json", stale)
        self._write("plan.2.json", good)
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)
        # ...and the reverse ordering yields no-claim, proving it is sequence order deciding
        # and not "any matching file anywhere wins".
        self._write("plan.2.json", stale)
        self._write("plan.1.json", good)
        self.assertIsNone(route.gate_mark(self.record, "plan", home=self.home))

    def test_history_sequence_is_numeric_not_lexical(self):
        good = self._marker("plan")
        stale = dict(good, route_hash="sha256:" + ("0" * 64))
        os.remove(os.path.join(self.cdir, "plan.json"))
        self._write("plan.9.json", stale)
        self._write("plan.10.json", good)   # lexical sort would pick "9"
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)

    def test_bad_inputs_never_raise(self):
        for bad_record in (None, "x", 123, {}, {"route_id": 1, "route_hash": 2}):
            with self.subTest(record=bad_record):
                self.assertIsNone(route.gate_mark(bad_record, "plan", home=self.home))
        for bad_node in (None, "", 123, [], {}):
            with self.subTest(node=bad_node):
                self.assertIsNone(route.gate_mark(self.record, bad_node, home=self.home))

    def test_node_id_never_traverses(self):
        self.assertIsNone(route.gate_mark(self.record, "../../plan", home=self.home))

    def test_cache_is_mtime_keyed(self):
        self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)
        with mock.patch("builtins.open", side_effect=AssertionError("re-read a cached marker")):
            self.assertIs(route.gate_mark(self.record, "plan", home=self.home), True)

    def test_home_defaults_to_agent_home_env(self):
        with mock.patch.dict(os.environ, {"AGENT_HOME": self.home}):
            self.assertIs(route.gate_mark(self.record, "plan"), True)

    def test_read_only_no_writes_to_completion_tree(self):
        before = {n: os.stat(os.path.join(self.cdir, n)).st_mtime_ns
                  for n in os.listdir(self.cdir)}
        route.resolve_gate_marks({self.route_id: self.record}, home=self.home)
        after = {n: os.stat(os.path.join(self.cdir, n)).st_mtime_ns
                 for n in os.listdir(self.cdir)}
        self.assertEqual(before, after)
        self.assertEqual(sorted(before), sorted(n + ".json" for n in _NODES))


class ResolveGateMarksTest(GateMarkBase):
    def test_resolve_returns_only_passed_nodes(self):
        os.remove(os.path.join(self.cdir, "report.json"))
        route.clear_cache()
        marks = route.resolve_gate_marks({self.route_id: self.record}, home=self.home)
        self.assertEqual(marks, {self.route_id: {"plan": True, "execute": True, "test": True}})

    def test_resolve_omits_route_with_no_marks(self):
        shutil.rmtree(self.cdir)
        route.clear_cache()
        self.assertEqual(route.resolve_gate_marks({self.route_id: self.record}, home=self.home), {})

    def test_resolve_tolerates_empty_and_none(self):
        self.assertEqual(route.resolve_gate_marks(None), {})
        self.assertEqual(route.resolve_gate_marks({}), {})


class BuildViewsGatePassedTest(GateMarkBase):
    """`build_views` must stay PURE — it consumes resolved marks, it never reads a marker."""

    def _view(self, gate_marks=None):
        views = route.build_views([], {}, {self.route_id: self.record}, 1_000_000.0, gate_marks)
        self.assertEqual(len(views), 1)
        return views[0]

    def test_default_is_no_claim_everywhere(self):
        v = self._view()
        self.assertEqual([n["gate_passed"] for n in v["nodes"]], [None] * 4)

    def test_marks_land_on_the_right_nodes(self):
        v = self._view({self.route_id: {"plan": True, "test": True}})
        got = {n["id"]: n["gate_passed"] for n in v["nodes"]}
        self.assertEqual(got, {"plan": True, "execute": None, "test": True, "report": None})

    def test_gate_passed_is_independent_of_state(self):
        """A `pending` node with a marker still reports passed, and a `done` node without one
        stays no-claim — proof the two dimensions are not derived from each other."""
        v = self._view({self.route_id: {"plan": True}})
        plan = next(n for n in v["nodes"] if n["id"] == "plan")
        self.assertEqual(plan["state"], "pending")
        self.assertIs(plan["gate_passed"], True)

    def test_build_views_does_no_io(self):
        with mock.patch("os.stat", side_effect=AssertionError("build_views touched the fs")), \
             mock.patch("builtins.open", side_effect=AssertionError("build_views touched the fs")):
            self._view({self.route_id: {"plan": True}})

    def test_collect_views_resolves_marks(self):
        with mock.patch.dict(os.environ, {"AGENT_HOME": self.home}), \
             mock.patch.object(route, "resolve_records",
                               return_value={self.route_id: self.record}):
            views = route.collect_views([], {}, now=1_000_000.0)
        self.assertEqual([n["gate_passed"] for n in views[0]["nodes"]], [True] * 4)

    def test_heuristic_view_has_no_nodes_to_mark(self):
        views = route.build_views([], {"rt-deadbeefdeadbeef": {}}, {}, 1_000_000.0)
        self.assertEqual(views[0]["source"], "heuristic")
        self.assertEqual(views[0]["nodes"], [])


class SummaryJsonTest(GateMarkBase):
    def test_gate_passed_is_additive_and_no_existing_key_moved(self):
        marks = {self.route_id: {"plan": True}}
        views = route.build_views([], {}, {self.route_id: self.record}, 1_000_000.0, marks)
        node = route.summary(views)[0]["nodes"][0]
        self.assertIn("gate_passed", node)
        self.assertIs(node["gate_passed"], True)
        # The v10 `--json` node key set, pinned verbatim — `gate_passed` is the ONLY addition.
        self.assertEqual(sorted(node), sorted([
            "id", "depends_on", "level", "state", "gate", "note",
            "elapsed_min", "model", "harness", "effort", "gate_passed"]))

    def test_unmarked_node_serializes_as_null_not_false(self):
        views = route.build_views([], {}, {self.route_id: self.record}, 1_000_000.0)
        node = route.summary(views)[0]["nodes"][0]
        self.assertIsNone(node["gate_passed"])
        self.assertIn('"gate_passed": null', json.dumps(node, indent=1))


class GateMarkRenderTest(unittest.TestCase):
    """The mark is a SEPARATE segment in `gate_t` — never folded into the state glyph's text
    (prd.md:308: an independent dimension), and never drawn for a no-claim node."""

    def _node(self, **kw):
        base = {"id": "plan", "state": "done", "level": 0, "elapsed_min": 12,
                "gate": "code-plan", "gate_passed": None, "model": None, "effort": None,
                "job": None, "depends_on": []}
        base.update(kw)
        return base

    def test_passed_node_emits_mark_segment(self):
        lines = render._route_card_l2({"nodes": [self._node(gate_passed=True)]})
        segs = lines[0]
        self.assertEqual(segs, [("plan ✓12m", "dim"), (render._GATE_MARK, "gate_t")])

    def test_no_claim_node_emits_no_mark(self):
        lines = render._route_card_l2({"nodes": [self._node()]})
        self.assertEqual(lines[0], [("plan ✓12m", "dim")])
        self.assertNotIn(render._GATE_MARK, "".join(t for t, _k in lines[0]))

    def test_mark_never_shares_the_state_glyph_colour(self):
        """The regression this guards: a dim `⊸` on a dim `done` node melts into one phrase
        (the merge render.py:101 warns about), which is why the mark owns `gate_t`."""
        for state in ("done", "pending", "failed"):
            with self.subTest(state=state):
                lines = render._route_card_l2({"nodes": [self._node(state=state,
                                                                    gate_passed=True)]})
                marks = [k for t, k in lines[0] if t == render._GATE_MARK]
                self.assertEqual(marks, ["gate_t"])

    def test_mark_survives_every_state(self):
        for state in ("done", "active", "failed", "pending"):
            with self.subTest(state=state):
                lines = render._route_card_l2({"nodes": [self._node(state=state,
                                                                    gate_passed=True)]})
                self.assertIn(render._GATE_MARK, [t for t, _k in lines[0]])

    def test_fan_out_branch_rows_carry_the_mark(self):
        nodes = [self._node(id="a", level=0, gate_passed=True),
                 self._node(id="b", level=0, gate_passed=None)]
        lines = render._route_card_l2({"nodes": nodes})
        self.assertEqual(len(lines), 2)
        self.assertIn(render._GATE_MARK, [t for t, _k in lines[0]])
        self.assertNotIn(render._GATE_MARK, [t for t, _k in lines[1]])

    def test_mark_width_is_accounted_when_cropping(self):
        """The mark must ride inside `_drop_past_stages`'s width math. Pinned at the exact width
        that separates the two behaviours: unmarked, this flow is 33 columns and `plan` (the only
        droppable past node) is kept; marked it is 37, so at 36 columns `plan` MUST fold. If the
        marks were excluded from the width math the folder would keep `plan` and then draw 37
        columns into a 36-column card — a silent one-column overflow per mark.

        Widths below the irreducible floor (the active node + everything after it, which
        `_drop_past_stages` never folds by design — SD-F2) are not asserted here: that is the
        breadcrumb's pre-existing contract, not this feature's."""
        nodes = [self._node(id="plan", level=0, gate_passed=True),
                 self._node(id="execute", level=1, state="active", elapsed_min=8,
                            gate_passed=True),
                 self._node(id="test", level=2, state="pending", elapsed_min=None)]
        bare = [dict(n, gate_passed=None) for n in nodes]

        def drawn(ns, width):
            lines = render._route_card_l2({"nodes": ns}, max_width=width)
            self.assertEqual(len(lines), 1)
            return "".join(t for t, _k in lines[0]), sum(render._dw(t) for t, _k in lines[0])

        text, w = drawn(bare, 36)
        self.assertEqual((w, "plan" in text), (33, True))   # baseline keeps `plan` at 36
        text, w = drawn(nodes, 36)
        self.assertNotIn("plan", text)                      # marked must fold it instead
        self.assertLessEqual(w, 36)

        for width in (30, 37, 60, 200):
            with self.subTest(width=width):
                _t, w = drawn(nodes, width)
                self.assertLessEqual(w, width, "L2 flow overflowed max_width")
        self.assertEqual(drawn(nodes, 37)[1], 37)           # fits exactly, nothing folded


class GateDetailRowTest(GateMarkBase):
    """The `a`-toggle `gates:` row — names always, `⊸` only where proven."""

    def _card(self, gate_marks):
        views = route.build_views([], {}, {self.route_id: self.record}, 1_000_000.0, gate_marks)
        out, _meta = render._route_card(views[0], {}, 120, 1_000_000.0)
        rows = [segs for segs in out
                if segs and isinstance(segs[0][0], str) and "gates: " in segs[0][0]]
        return rows

    def test_gates_row_hidden_without_show_all(self):
        render.set_show_all(False)
        try:
            self.assertEqual(self._card({self.route_id: {"plan": True}}), [])
        finally:
            render.set_show_all(False)

    def test_gates_row_marks_only_passed_gates(self):
        render.set_show_all(True)
        try:
            rows = self._card({self.route_id: {"plan": True, "report": True}})
            self.assertEqual(len(rows), 1)
            segs = rows[0]
            text = "".join(t for t, _k in segs)
            self.assertEqual(text, "      gates: code-plan ⊸, code-execute, code-test, "
                                   "code-report ⊸")
            self.assertEqual([k for t, k in segs if t == render._GATE_MARK],
                             ["gate_t", "gate_t"])
        finally:
            render.set_show_all(False)

    def test_gates_row_unmarked_shows_bare_names(self):
        render.set_show_all(True)
        try:
            segs = self._card({})[0]
            self.assertEqual("".join(t for t, _k in segs),
                             "      gates: code-plan, code-execute, code-test, code-report")
        finally:
            render.set_show_all(False)


if __name__ == "__main__":
    unittest.main()
