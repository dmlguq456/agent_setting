#!/usr/bin/env python3
"""Hermetic unit tests — F-28b route-aware breadcrumb (render.py `_stage_segs`/
`_dispatch_stage_segs`/`_conductor_route_seq`/`_conductor_stage_override`).

T2-1 is the regression pin: a record-less job's breadcrumb must be BYTE-IDENTICAL to the
pre-v10 `_PIPE_STAGES` path — route_seq is purely additive.
"""
import os
import sys
import unittest

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import render                    # noqa: E402
from fleet import route                     # noqa: E402
from fleet.collectors import dispatch       # noqa: E402
from fleet.model import DispatchJob         # noqa: E402

_FIXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "route")
_REAL_CLAUDE = os.path.join(_FIXDIR, "real_claude_staged.json")
_REAL_RID = "rt-27f7bc9ff152ba13"
_LAB = os.path.join(_FIXDIR, "synth_parallel_lab.json")


def _joined(lines):
    return "\n".join("".join(t for t, _k in ln) for ln in lines if ln)


class RouteBreadcrumbTest(unittest.TestCase):
    def setUp(self):
        route.clear_cache()
        self._saved_evidence = dispatch.collect.last_route_nodes
        dispatch.collect.last_route_nodes = {}

    def tearDown(self):
        dispatch.collect.last_route_nodes = self._saved_evidence
        route.clear_cache()

    def test_t2_1_record_less_job_matches_pre_v10_breadcrumb_exactly(self):
        job = DispatchJob(key="code", stage="exec", slug="no-route-job", cwd="/x",
                          liveness="working", depth=1)
        via_build_lines = _joined(
            render._build_lines([], [job], section="dispatch", narrow=False,
                                malformed=0, layout="wide"))
        direct = render._dispatch_stage_segs(job, "code", "exec", "no-route-job", working=True)
        expected_text = "".join(t for t, _k in direct)
        self.assertIn(expected_text, via_build_lines)
        # explicit sanity: the OLD 3-stage `_PIPE_STAGES` vocabulary is what rendered — not a
        # record node id (there is no record here at all).
        self.assertIn("exec", expected_text)

    def test_t2_2_real_record_lights_active_child_node(self):
        dispatch.collect.last_route_nodes = {
            _REAL_RID: {"plan": {"status": "done", "slug": "v10-plan", "ts": None,
                                 "note": None, "model": "opus", "harness": "claude",
                                 "effort": "high", "completion_gate": "code-plan"}},
        }
        conductor = DispatchJob(key="code", slug="v10-conductor", cwd="/x", depth=1,
                                liveness="working", capability_owner="autopilot-code")
        child = DispatchJob(key="code-execute", slug="v10-conductor-execute", cwd="/x",
                            parent_slug="v10-conductor", depth=2, liveness="working",
                            route_id=_REAL_RID, route_file=_REAL_CLAUDE, route_node="execute")
        text = _joined(render._build_lines([], [conductor, child], section="dispatch",
                                           narrow=False, malformed=0, layout="wide"))
        # _STAGE_ZONE_MAX(30) crops PAST stages first (SD-F2, unchanged _drop_past_stages) —
        # "plan✓" folds away here exactly like a 4-stage `_PIPE_STAGES` breadcrumb would, so
        # what survives is the active node onward, using the RECORD's own node id ("execute",
        # not the `_PIPE_STAGES` "exec" abbreviation).
        self.assertIn("execute", text)
        self.assertIn("test", text)
        self.assertIn("report", text)
        # the underlying route_seq itself DOES carry plan as done — verified unit-level,
        # independent of the width crop above.
        views = route.build_views([child], dispatch.collect.last_route_nodes,
                                  {_REAL_RID: route.load(_REAL_CLAUDE)}, now=0.0)
        plan_node = next(n for n in views[0]["nodes"] if n["id"] == "plan")
        self.assertEqual(plan_node["state"], "done")

    def test_t2_3_non_pipe_stages_node_labels_render_without_crashing(self):
        dispatch.collect.last_route_nodes = {}
        lab_rid = "rt-6f5423d05eaf3189"
        conductor = DispatchJob(key="lab", slug="lab-conductor", cwd="/x", depth=1,
                                liveness="working")
        child = DispatchJob(key="lab-eval", slug="lab-conductor-eval-sep", cwd="/x",
                            parent_slug="lab-conductor", depth=2, liveness="working",
                            route_id=lab_rid, route_file=_LAB, route_node="eval-sep")
        text = _joined(render._build_lines([], [conductor, child], section="dispatch",
                                           narrow=False, malformed=0, layout="wide"))
        self.assertIn("eval-sep", text)

    def test_t2_4_record_with_zero_live_children_stays_unlit(self):
        # SD-F2 — record presence alone never lights a node; only live evidence does.
        dispatch.collect.last_route_nodes = {}
        conductor = DispatchJob(key="code", slug="v10-idle-conductor", cwd="/x", depth=1,
                                liveness="idle")
        child = DispatchJob(key="code-plan", slug="v10-idle-conductor-plan", cwd="/x",
                            parent_slug="v10-idle-conductor", depth=2, liveness="idle",
                            route_id=_REAL_RID, route_file=_REAL_CLAUDE, route_node="plan")
        views = route.collect_views([child], dispatch.collect.last_route_nodes)
        self.assertEqual(views[0]["nodes"][0]["state"], "pending")

    def test_t2_5_narrow_width_overflow_zero(self):
        node_view = [(n, "pending") for n in ("plan", "execute", "test", "report")]
        segs = render._stage_segs("code", "", working=False,
                                  max_width=render._STAGE_ZONE_MAX, route_seq=node_view)
        width = sum(render._dw(t) for t, _k in segs)
        self.assertLessEqual(width, render._STAGE_ZONE_MAX)

    def test_t2_6_autopilot_spec_research_node_renders(self):
        segs = render._dispatch_stage_segs(
            DispatchJob(key="spec-research", slug="v94-note-db-steward-research", depth=1),
            "spec-research", "research", "v94-note-db-steward-research", working=True,
            route_seq=[("research", "active")])
        text = "".join(t for t, _k in segs)
        self.assertEqual(text, "research")


if __name__ == "__main__":
    unittest.main()
