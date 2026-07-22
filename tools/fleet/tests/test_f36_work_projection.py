"""Focused F-36 projection and sealed composed-DAG acceptance checks."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import projection, render, route  # noqa: E402
from fleet.model import DispatchJob, Session  # noqa: E402


FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "route")
COMPOSED = os.path.join(FIXTURES, "synth_composed_survey.json")
REAL = os.path.join(FIXTURES, "real_claude_staged.json")


class WorkProjectionTest(unittest.TestCase):
    def test_session_owner_render_shows_all_parallel_siblings_in_sealed_order(self):
        record = route.load(COMPOSED)
        rid = record["route_id"]
        owner = Session(harness="claude", pid=100, proc_start="owner-start",
                        cwd="/home/proj", slug="main", session_id="sid-owner",
                        liveness="working", elapsed_min=12, branch="main")
        # Reverse collector/jobs input order deliberately.  The attached route view
        # must still expose the sealed record order claim-a, claim-b.
        jobs = [
            DispatchJob(key="claim", slug="claim-b", parent_sid="sid-owner", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-b",
                        assigned_contract="autopilot-code", liveness="working",
                        harness="claude", pid=102, proc_start="child-b"),
            DispatchJob(key="claim", slug="claim-a", parent_sid="sid-owner", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-a",
                        assigned_contract="autopilot-code", liveness="working",
                        harness="claude", pid=101, proc_start="child-a"),
        ]
        projection.attach_projections([owner], jobs, now=100.0)
        self.assertEqual(owner.work_projection.stage_label, "{claim-a,claim-b}")
        render.set_process_view(False)
        try:
            for width in (168, 120, 100, 60):
                lines = render._build_lines(
                    [owner], jobs, section="both", narrow=width < 70,
                    malformed=0, layout=render._layout_mode(width), term_width=width,
                )
                text = "\n".join(
                    "".join(token for token, _kind in line)
                    for line in lines if line
                ).replace("\x00", "")
                with self.subTest(width=width):
                    self.assertIn("claim-a", text)
                    self.assertIn("claim-b", text)
                    self.assertIn("{claim-a,claim-b}", text)
                    self.assertNotIn("stage autopilot-code", text)
        finally:
            render.set_process_view(False)

    def test_owner_stage_label_uses_node_ids_for_generic_single_and_parallel_children(self):
        rid = route.load(REAL)["route_id"]
        single_owner = DispatchJob(key="owner", slug="single-owner", depth=1,
                                   liveness="working")
        single = DispatchJob(
            key="code", slug="single-child", parent_slug="single-owner", depth=2,
            route_id=rid, route_file=REAL, route_node="execute",
            assigned_contract="autopilot-code", liveness="working")
        parallel_owner = DispatchJob(key="owner", slug="parallel-owner", depth=1,
                                     liveness="working")
        first = DispatchJob(
            key="code", slug="parallel-a", parent_slug="parallel-owner", depth=2,
            route_id=route.load(COMPOSED)["route_id"], route_file=COMPOSED,
            route_node="claim-a", assigned_contract="autopilot-code",
            liveness="working")
        second = DispatchJob(
            key="code", slug="parallel-b", parent_slug="parallel-owner", depth=2,
            route_id=route.load(COMPOSED)["route_id"], route_file=COMPOSED,
            route_node="claim-b", assigned_contract="autopilot-code",
            liveness="working")
        projection.attach_projections([], [single_owner, single, parallel_owner, second, first], now=100.0)
        self.assertEqual(single_owner.work_projection.stage_label, "execute")
        self.assertEqual(parallel_owner.work_projection.stage_label, "{claim-a,claim-b}")

    def test_sealed_composed_dag_preserves_opaque_siblings_fanin_and_scope(self):
        record = route.load(COMPOSED)
        rid = record["route_id"]
        jobs = [
            DispatchJob(key="claim", slug="claim-a", parent_slug="owner", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-a",
                        liveness="working"),
            DispatchJob(key="claim", slug="claim-b", parent_slug="owner", depth=2,
                        route_id=rid, route_file=COMPOSED, route_node="claim-b",
                        liveness="working"),
        ]
        owner = DispatchJob(key="analyze", slug="owner", depth=1, liveness="working")
        projection.attach_projections([], jobs + [owner], now=100.0)
        self.assertEqual({n.id for n in owner.work_projection.active_nodes}, {"claim-a", "claim-b"})
        view = owner.work_projection._route_view["view"]
        levels = [[n["id"] for n in view["nodes"] if n["level"] == level]
                  for level in range(3)]
        self.assertEqual(levels[0], ["survey"])
        self.assertEqual(levels[1], ["claim-a", "claim-b"])
        self.assertEqual(levels[2], ["synth"])
        claim_a = next(n for n in view["nodes"] if n["id"] == "claim-a")
        self.assertEqual(claim_a["write_scope"], ["reviews/claim-a/**"])
        self.assertNotIn("plan", {n["id"] for n in view["nodes"]})

    def test_exact_route_beats_artifact_and_public_route_is_json_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "plans", "2026-07-22_exact-job", "test"))
            entity = DispatchJob(key="code", slug="exact-job", cwd=tmp,
                                 route_id="rt-27f7bc9ff152ba13", route_file=REAL,
                                 route_node="execute", liveness="working")
            projection.attach_projections([], [entity], artifact_root=tmp, now=100.0)
            self.assertEqual(entity.work_projection.source, "route-exact")
            self.assertEqual(entity.work_projection.stage_label, "execute")
            payload = projection.route_summary_from_projections([entity])
            json.dumps(payload)
            self.assertEqual(payload[0]["nodes"][1]["id"], "execute")
            self.assertNotIn("job", payload[0]["nodes"][1])

    def test_invalid_explicit_route_fails_closed_over_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "plans", "2026-07-22_bad-job", "test"))
            entity = DispatchJob(key="code", slug="bad-job", cwd=tmp,
                                 route_id="rt-mismatch", route_file=REAL,
                                 route_node="execute", liveness="working")
            projection.attach_projections([], [entity], artifact_root=tmp, now=100.0)
            self.assertEqual(entity.work_projection.source, "registry-exact")
            self.assertEqual(entity.work_projection.ambiguity, "route-record-mismatch")
            self.assertNotEqual(entity.work_projection.source, "artifact-inferred")

    def test_artifact_cardinality_is_exact_and_stage_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "plans", "2026-07-22_unique-job", "execute"))
            entity = DispatchJob(key="code", slug="unique-job", cwd=tmp)
            projection.attach_projections([], [entity], artifact_root=tmp, now=100.0)
            self.assertEqual(entity.work_projection.source, "artifact-inferred")
            self.assertIsNone(entity.work_projection.route_id)
            self.assertIsNone(entity.work_projection.progress)
            os.makedirs(os.path.join(tmp, "plans", "2026-07-22_second_unique-job", "test"))
            self.assertEqual(len(projection.exact_artifact_candidates(entity, tmp)), 2)
            projection.attach_projections([], [entity], artifact_root=tmp, now=100.0)
            self.assertEqual(entity.work_projection.ambiguity, "multiple-artifact-plan-dirs")

    def test_owner_rejects_different_child_routes(self):
        other = route.load(REAL)
        rid = route.load(COMPOSED)["route_id"]
        first = DispatchJob(key="claim", slug="a", parent_slug="owner", depth=2,
                            route_id=rid, route_file=COMPOSED, route_node="claim-a",
                            liveness="working")
        second = DispatchJob(key="code", slug="b", parent_slug="owner", depth=2,
                             route_id=other["route_id"], route_file=REAL, route_node="execute",
                             liveness="working")
        owner = DispatchJob(key="analyze", slug="owner", depth=1, liveness="working")
        projection.attach_projections([], [first, second, owner], now=100.0)
        self.assertEqual(owner.work_projection.ambiguity, "multiple-owner-routes")

    def test_same_process_identity_with_two_leaf_routes_fails_closed(self):
        first = DispatchJob(key="code", slug="a", pid=55, proc_start="start",
                            route_id="route-a", route_node="execute")
        second = DispatchJob(key="code", slug="b", pid=55, proc_start="start",
                             route_id="route-b", route_node="test")
        projection.attach_projections([], [first, second], now=100.0)
        self.assertEqual(first.work_projection.ambiguity, "multiple-leaf-candidates")

    def test_unique_exact_and_unique_cwd_candidates_are_adopted(self):
        rid = route.load(REAL)["route_id"]
        leaf = DispatchJob(key="code", slug="leaf", pid=71, proc_start="new",
                           cwd="/route", harness="claude", route_id=rid,
                           route_file=REAL, route_node="execute", liveness="working")
        exact = Session(harness="claude", pid=71, proc_start="new", cwd="/other",
                        session_id="sid-exact", liveness="working")
        cwd = Session(harness="claude", pid=72, proc_start=None, cwd="/route",
                      session_id="sid-cwd", liveness="working")
        projection.attach_projections([exact, cwd], [leaf], now=100.0)
        self.assertEqual((exact.work_projection.source, exact.work_projection.route_node),
                         ("route-exact", "execute"))
        self.assertEqual((cwd.work_projection.source, cwd.work_projection.route_node),
                         ("route-exact", "execute"))

    def test_pid_reuse_and_duplicate_cwd_candidates_refuse_adoption(self):
        rid = route.load(REAL)["route_id"]
        reused = DispatchJob(key="code", slug="reused", pid=71, proc_start="new",
                             cwd="/same", harness="claude", route_id=rid,
                             route_file=REAL, route_node="execute", liveness="working")
        stale_identity = Session(harness="claude", pid=71, proc_start="old", cwd="/same",
                                 session_id="sid-reused", liveness="working")
        projection.attach_projections([stale_identity], [reused], now=100.0)
        self.assertNotEqual(stale_identity.work_projection.source, "route-exact")
        self.assertIsNone(stale_identity.work_projection.route_id)

        first = DispatchJob(key="code", slug="cwd-a", cwd="/same", harness="claude",
                            route_id=rid, route_file=REAL, route_node="plan", liveness="working")
        second = DispatchJob(key="code", slug="cwd-b", cwd="/same", harness="claude",
                             route_id=rid, route_file=REAL, route_node="execute", liveness="working")
        ambiguous = Session(harness="claude", pid=73, cwd="/same", session_id="sid-cwd",
                            liveness="working")
        projection.attach_projections([ambiguous], [first, second], now=100.0)
        self.assertEqual(ambiguous.work_projection.ambiguity,
                         "multiple-child-cwd-candidates")

    def test_attempt_only_and_both_owner_link_contracts_traverse_children(self):
        rid = route.load(REAL)["route_id"]
        session_owner = Session(harness="claude", pid=80, cwd="/owner", session_id="sid-owner",
                                liveness="working")
        session_child = DispatchJob(key="code", slug="sid-child", parent_sid="sid-owner",
                                    route_id=rid, route_file=REAL, route_node="execute",
                                    liveness="working")
        dispatch_owner = DispatchJob(key="code", slug="slug-owner", attempt_id="att-only",
                                     depth=1, liveness="working")
        dispatch_child = DispatchJob(key="code", slug="slug-child", parent_slug="slug-owner",
                                     depth=2, route_id=rid, route_file=REAL, route_node="execute",
                                     liveness="working")
        projection.attach_projections([session_owner],
                                      [session_child, dispatch_owner, dispatch_child], now=100.0)
        self.assertEqual(session_owner.work_projection.source, "route-exact")
        self.assertEqual(dispatch_owner.work_projection.source, "route-exact")
        self.assertEqual(dispatch_owner.work_projection.stage_label, "execute")

    def test_direct_owner_route_conflict_is_fail_closed(self):
        owner_record = route.load(REAL)
        child_record = route.load(COMPOSED)
        owner = DispatchJob(key="owner", slug="owner", depth=1,
                            route_id=owner_record["route_id"], route_file=REAL,
                            route_node="execute", liveness="working")
        child = DispatchJob(key="claim", slug="child", parent_slug="owner", depth=2,
                            route_id=child_record["route_id"], route_file=COMPOSED,
                            route_node="claim-a", liveness="working")
        projection.attach_projections([], [owner, child], now=100.0)
        self.assertEqual(owner.work_projection.ambiguity, "owner-route-conflict")
        self.assertIsNone(owner.work_projection.route_id)

    def test_old_route_keys_and_private_evidence_remain_compatible(self):
        rid = route.load(REAL)["route_id"]
        job = DispatchJob(key="code", slug="old-consumer", route_id=rid, route_file=REAL,
                          route_node="execute", model="opus", harness="claude", effort="high",
                          liveness="working")
        projection.attach_projections([], [job], now=100.0)
        payload = projection.route_summary_from_projections([job])[0]
        node = next(item for item in payload["nodes"] if item["id"] == "execute")
        self.assertEqual(payload["source"], "record")
        self.assertEqual({key: node[key] for key in ("model", "harness", "effort", "elapsed_min", "note")},
                         {"model": "opus", "harness": "claude", "effort": "high",
                          "elapsed_min": None, "note": None})
        self.assertIsInstance(job.to_dict()["work_projection"]["ambiguity"], list)
        self.assertNotIn("_context_evidence", json.dumps(job.to_dict()))

    def test_qa_artifact_lookup_is_exact_and_separate_from_stage(self):
        from fleet.collectors import dispatch
        with tempfile.TemporaryDirectory() as tmp:
            plan = os.path.join(tmp, ".agent_reports", "plans", "2026-07-22_qa-job")
            os.makedirs(os.path.join(plan, "plan"))
            with open(os.path.join(plan, "plan", "plan.md"), "w", encoding="utf-8") as stream:
                stream.write("qa_level: standard\n")
            job = DispatchJob(key="code", slug="qa-job", cwd=tmp)
            self.assertEqual(dispatch.resolve_plan_qa_artifact(job), "standard")


if __name__ == "__main__":
    unittest.main()
