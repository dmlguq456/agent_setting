#!/usr/bin/env python3
"""Hermetic unit tests — F-28a route record consumption (route.py + dispatch.py collector
edits + fleet.py --json). Stdlib unittest only, tempfile.TemporaryDirectory + mock (test_dispatch.py
precedent). No real dispatch/record I/O outside the copied fixtures under tests/fixtures/route/.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from fleet import route                     # noqa: E402
from fleet.collectors import dispatch       # noqa: E402
from fleet.model import DispatchJob         # noqa: E402

_FIXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "route")


def _fx(name):
    return os.path.join(_FIXDIR, name)


class RouteLoadTest(unittest.TestCase):
    def setUp(self):
        route.clear_cache()

    def tearDown(self):
        route.clear_cache()

    def test_t1_1_load_real_claude(self):
        rec = route.load(_fx("real_claude_staged.json"))
        self.assertIsInstance(rec, dict)
        self.assertEqual(rec["route_id"], "rt-27f7bc9ff152ba13")

    def test_t1_2_load_real_codex(self):
        rec = route.load(_fx("real_codex_staged.json"))
        self.assertIsInstance(rec, dict)
        self.assertEqual(rec["route_id"], "rt-1120bb39a13c4191")

    def test_t1_3_load_missing_path_never_raises(self):
        rec = route.load("/no/such/path/route.json")
        self.assertIsNone(rec)

    def test_t1_3b_non_path_like_input_never_raises(self):
        # I2 regression pin — found during Step 5 integration sweep: os.path.abspath(123)
        # raised TypeError, which a malformed pipe-parse value could theoretically reach.
        for bad in (123, 1.5, {}, [], object(), b"", ()):
            with self.subTest(bad=bad):
                self.assertIsNone(route.load(bad))

    def test_t1_4_hash_recompute_matches_both_real_records(self):
        for name in ("real_claude_staged.json", "real_codex_staged.json"):
            with open(_fx(name), encoding="utf-8") as f:
                rec = json.load(f)
            self.assertEqual(route.route_hash(rec), rec["route_hash"], name)

    def test_t1_5_broken_hash_rejected(self):
        self.assertIsNone(route.load(_fx("synth_broken_hash.json")))

    def test_t1_6_bad_schema_rejected(self):
        self.assertIsNone(route.load(_fx("synth_bad_schema.json")))

    def test_t1_7_pipe_hash_mismatch_rejected(self):
        rec = route.load(_fx("real_claude_staged.json"), expect_hash="sha256:deadbeef")
        self.assertIsNone(rec)

    def test_t1_8_cache_hit_skips_second_json_load(self):
        route.clear_cache()
        with mock.patch("fleet.route.json.load", wraps=json.load) as m:
            route.load(_fx("real_claude_staged.json"))
            route.load(_fx("real_claude_staged.json"))
            self.assertEqual(m.call_count, 1)

    def test_t1_9_cache_invalidates_on_mtime_change(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "r.json")
            shutil.copy(_fx("real_claude_staged.json"), path)
            rec1 = route.load(path)
            self.assertIsNotNone(rec1)
            # rewrite with the OTHER real record (different mtime+size+content)
            shutil.copy(_fx("real_codex_staged.json"), path)
            os.utime(path, None)
            rec2 = route.load(path)
            self.assertIsNotNone(rec2)
            self.assertNotEqual(rec1["route_id"], rec2["route_id"])

    def test_current_route_rejects_declared_max_below_realized_depth(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "route.json")
            record = {
                "schema_version": 2,
                "dispatch_contract_version": 3,
                "owner_dispatch_depth": 1,
                "max_dispatch_depth": 1,
                "nodes": [{
                    "id": "execute",
                    "dispatch_depth": 2,
                }],
            }
            record["route_hash"] = route.route_hash(record)
            record["route_id"] = (
                "rt-" + record["route_hash"].split(":", 1)[1][:16]
            )
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(record, handle)
            self.assertIsNone(route.load(path))


class NodeOrderTest(unittest.TestCase):
    def test_t1_10_parallel_lab_levels(self):
        with open(_fx("synth_parallel_lab.json"), encoding="utf-8") as f:
            rec = json.load(f)
        levels = route.node_order(rec)
        self.assertEqual(levels, [
            ["setup"], ["eval-asr", "eval-sep", "eval-vad"], ["aggregate"], ["report"],
        ])

    def test_t1_11_cycle_never_raises_and_keeps_all_nodes(self):
        rec = {"nodes": [
            {"id": "a", "depends_on": ["b"]},
            {"id": "b", "depends_on": ["a"]},
            {"id": "c", "depends_on": []},
        ]}
        levels = route.node_order(rec)
        seen = [nid for level in levels for nid in level]
        self.assertEqual(sorted(seen), ["a", "b", "c"])


def _write_jobs_route_log(tmpdir):
    with open(_fx("jobs_route.log"), encoding="utf-8") as f:
        template = f.read()
    content = template.format(FIXDIR=_FIXDIR)
    path = os.path.join(tmpdir, "jobs.log")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class CollectRouteFieldsTest(unittest.TestCase):
    def setUp(self):
        route.clear_cache()

    def tearDown(self):
        # module-global stash (dispatch.collect.last_route_nodes) must never leak into a
        # later test that reads it without collecting first (JsonAdditiveTest below).
        dispatch.collect.last_route_nodes = {}

    def test_t1_12_jobs_carry_route_fields_even_when_record_gone(self):
        with tempfile.TemporaryDirectory() as td:
            jobs_path = _write_jobs_route_log(td)
            with mock.patch.object(dispatch.procscan, "_ps_lines", return_value=[]):
                jobs = dispatch.collect(jobs_path=jobs_path)
            by_slug = {j.slug: j for j in jobs}
            self.assertIn("fleet-v10-plan", by_slug)
            self.assertEqual(by_slug["fleet-v10-plan"].route_id, "rt-27f7bc9ff152ba13")
            self.assertEqual(by_slug["fleet-v10-plan"].route_node, "plan")
            # v94-note-db-steward-research: route_file points at a real-world path this
            # checkout cannot resolve — the job itself must still be alive (tolerant §3.3).
            self.assertIn("v94-note-db-steward-research", by_slug)
            self.assertEqual(by_slug["v94-note-db-steward-research"].route_id,
                             "rt-5e123969aa5a202b")

    def test_t1_13_terminal_route_node_survives_as_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            jobs_path = _write_jobs_route_log(td)
            with mock.patch.object(dispatch.procscan, "_ps_lines", return_value=[]):
                dispatch.collect(jobs_path=jobs_path)
            nodes = dispatch.collect.last_route_nodes
            self.assertIn("rt-27f7bc9ff152ba13", nodes)
            self.assertNotIn("plan", ())  # sanity no-op guard
            # Historical terminal rows remain diagnostic history, but cannot
            # authoritatively set current route-node state.
            report = nodes["rt-9ff8199b5372cfdb"]["report"]
            test = nodes["rt-1120bb39a13c4191"]["test"]
            self.assertNotIn("status", report)
            self.assertNotIn("status", test)
            self.assertEqual(
                report["attempt_history"][-1]["contract_status"], "legacy-read-only"
            )
            self.assertEqual(
                test["attempt_history"][-1]["contract_status"], "legacy-read-only"
            )

    def test_t1_13b_terminal_only_route_still_resolves_to_a_record_not_heuristic(self):
        """code-test verification.md §10 — the exact defect: `v93-reading-face-d1-test-r6`
        (rt-1120bb39a13c4191) is a DONE row in the fixture — `dispatch.collect()`'s returned
        `jobs` therefore carries NO live job for that route_id (the row never survives
        `_scan_jobs_log`'s terminal-row filter). Before the fix, `route.collect_views()` had no
        way to find `real_codex_staged.json` at all in that situation and produced a
        `source="heuristic", nodes=[]` degrade view for a perfectly valid, hash-verified
        record — this pins the fix (`_scan_route_nodes` now carries `route_file` in its
        evidence, and `resolve_records` consults it when no live job does)."""
        route.clear_cache()
        with tempfile.TemporaryDirectory() as td:
            jobs_path = _write_jobs_route_log(td)
            with mock.patch.object(dispatch.procscan, "_ps_lines", return_value=[]):
                jobs = dispatch.collect(jobs_path=jobs_path)
            self.assertFalse(any(j.route_id == "rt-1120bb39a13c4191" for j in jobs),
                             "fixture precondition: this route has no LIVE job at all")
            views = route.collect_views(jobs, dispatch.collect.last_route_nodes)
        view = next(v for v in views if v["route_id"] == "rt-1120bb39a13c4191")
        self.assertEqual(view["source"], "heuristic")
        self.assertEqual(view["nodes"], [])


class BuildViewsTest(unittest.TestCase):
    def setUp(self):
        with open(_fx("synth_parallel_lab.json"), encoding="utf-8") as f:
            self.record = json.load(f)
        self.route_id = self.record["route_id"]
        self.now = 1_800_000_000.0

    def test_t1_14_active_beats_done(self):
        job = DispatchJob(key="eval-asr", slug="lab-eval-asr", route_id=self.route_id,
                          route_node="eval-asr", liveness="working", elapsed_min=8,
                          model="sonnet", effort="medium", pid=555)
        ev = {self.route_id: {"eval-asr": {"status": "done", "slug": "lab-eval-asr-old",
                                           "ts": self.now - 600, "note": None}}}
        views = route.build_views([job], ev, {self.route_id: self.record}, self.now)
        self.assertEqual(len(views), 1)
        node = next(n for n in views[0]["nodes"] if n["id"] == "eval-asr")
        self.assertEqual(node["state"], "active")

    def test_t1_15_failed_registry_row(self):
        ev = {self.route_id: {"eval-sep": {"status": "done", "slug": "lab-eval-sep",
                                           "ts": self.now - 300, "note": "fleet-kill"}}}
        views = route.build_views([], ev, {self.route_id: self.record}, self.now)
        node = next(n for n in views[0]["nodes"] if n["id"] == "eval-sep")
        self.assertEqual(node["state"], "failed")

    def test_pending_when_no_evidence(self):
        views = route.build_views([], {}, {self.route_id: self.record}, self.now)
        node = next(n for n in views[0]["nodes"] if n["id"] == "report")
        self.assertEqual(node["state"], "pending")

    def test_heuristic_view_when_record_unresolved(self):
        job = DispatchJob(key="x", slug="x", route_id="rt-unknown0000000")
        views = route.build_views([job], {}, {}, self.now)
        self.assertEqual(views[0]["source"], "heuristic")
        self.assertEqual(views[0]["nodes"], [])

    def test_current_unit_metadata_survives_view_and_json_summary(self):
        record = json.loads(json.dumps(self.record))
        record["unit_catalog_digest"] = "sha256:" + "a" * 64
        record["composed"] = True
        record["nodes"][0]["unit"] = "code-plan"
        record["nodes"][0]["unit_choices"] = ["code-plan", "spec-plan"]
        views = route.build_views([], {}, {self.route_id: record}, self.now)
        view = views[0]
        node = next(n for n in view["nodes"] if n["id"] == record["nodes"][0]["id"])
        self.assertEqual(view["unit_catalog_digest"], record["unit_catalog_digest"])
        self.assertTrue(view["composed"])
        self.assertEqual(node["unit"], "code-plan")
        self.assertEqual(node["unit_choices"], ["code-plan", "spec-plan"])
        projected = route.summary(views)[0]
        self.assertEqual(projected["unit_catalog_digest"], record["unit_catalog_digest"])
        self.assertTrue(projected["composed"])
        self.assertEqual(projected["nodes"][0]["unit"], "code-plan")

    def test_legacy_route_metadata_defaults_are_additive(self):
        views = route.build_views([], {}, {self.route_id: self.record}, self.now)
        projected = route.summary(views)[0]
        self.assertIsNone(projected["unit_catalog_digest"])
        self.assertFalse(projected["composed"])
        self.assertTrue(all(node["unit"] is None for node in projected["nodes"]))

    def test_malformed_unit_metadata_degrades_without_string_explosion(self):
        record = json.loads(json.dumps(self.record))
        record["nodes"][0]["unit"] = {"not": "a unit id"}
        record["nodes"][0]["unit_choices"] = "code-plan"
        view = route.build_views([], {}, {self.route_id: record}, self.now)[0]
        node = next(n for n in view["nodes"] if n["id"] == record["nodes"][0]["id"])
        self.assertIsNone(node["unit"])
        self.assertEqual(node["unit_choices"], [])


class JsonAdditiveTest(unittest.TestCase):
    def setUp(self):
        route.clear_cache()
        dispatch.collect.last_route_nodes = {}   # test isolation — no leaked module state

    def test_t1_16_route_key_additive(self):
        if __package__:
            pass
        from fleet import fleet as fleetmod
        sessions, jobs = [], []
        out = json.loads(fleetmod._snapshot_json(sessions, jobs))
        self.assertIn("sessions", out)
        self.assertIn("jobs", out)
        self.assertIn("summary", out)
        self.assertIn("route", out)
        self.assertEqual(out["route"], [])

    def test_t1_17_no_route_records_empty_array(self):
        from fleet import fleet as fleetmod
        job = DispatchJob(key="code", slug="no-route-job")   # no route_id at all
        out = json.loads(fleetmod._snapshot_json([], [job]))
        self.assertEqual(out["route"], [])
        self.assertIn("route_file", out["jobs"][0])   # additive per-job keys present
        self.assertIsNone(out["jobs"][0]["route_file"])
        self.assertIn("unit", out["jobs"][0])
        self.assertIsNone(out["jobs"][0]["unit"])


class OrphanConductorAnnotationTest(unittest.TestCase):
    """SD-64/71: Fleet's current-attempt view stamps note/resume_boundary on a
    dead depth-1 owner row that the shared registry classifier detects as
    orphaned, reusing dispatch-registry.py's classify() in-process."""

    def setUp(self):
        route.clear_cache()
        dispatch.collect.last_route_nodes = {}
        dispatch._ORPHAN_REGISTRY_MOD = None

    def _write_route(self, td, route_id):
        record = {"route_id": route_id, "nodes": [
            {"id": "plan", "depends_on": []}, {"id": "execute", "depends_on": ["plan"]},
            {"id": "test", "depends_on": ["execute"]}, {"id": "report", "depends_on": ["test"]}]}
        path = os.path.join(td, "route.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh)
        return path

    def test_dead_owner_with_open_child_is_stamped_orphaned(self):
        with tempfile.TemporaryDirectory() as td:
            home = os.path.join(td, "home")
            marker_dir = os.path.join(home, ".dispatch", "completion", "rt-fleet-orphan")
            os.makedirs(marker_dir)
            with open(os.path.join(marker_dir, "plan.json"), "w", encoding="utf-8") as fh:
                json.dump({"node_id": "plan"}, fh)
            route_file = self._write_route(td, "rt-fleet-orphan")
            jobs_path = os.path.join(td, "jobs.log")
            with open(jobs_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "2026-07-19T00:00:00Z\topen\t/r\t/w\towner\t"
                    "worker_type=owner,attempt_id=att-fleet-owner,"
                    "pid=999999996,pid_start=1,attempt_schema_version=2,"
                    "dispatch_depth=1,transport=headless,"
                    "execution_surface=registered-headless,registered_worker=1,"
                    "fallback_hop=same-harness-headless\n"
                )
                # No pid/pid_start is needed here: the registry contract counts any open
                # exact child row and preserves it for main-session diagnosis.
                fh.write(
                    "2026-07-19T00:00:01Z\topen\t/r\t/w\tchild\t"
                    "route_id=rt-fleet-orphan,route_file=%s,route_node=execute,"
                    "attempt_id=att-fleet-child,parent=owner,"
                    "attempt_schema_version=2,dispatch_depth=2,transport=headless,"
                    "execution_surface=registered-headless,registered_worker=1,"
                    "fallback_hop=same-harness-headless\n" % route_file
                )
            with mock.patch.object(dispatch.procscan, "_ps_lines", return_value=[]), \
                 mock.patch.dict(os.environ, {"AGENT_HOME": home}):
                jobs = dispatch.collect(jobs_path=jobs_path)
            owner = next(j for j in jobs if j.slug == "owner")
            self.assertEqual(owner.liveness, "dead")
            self.assertEqual(owner.note, "dead-parent-orphaned")
            self.assertEqual(owner.resume_boundary, "execute")

    def test_dead_owner_with_completed_route_is_never_stamped(self):
        with tempfile.TemporaryDirectory() as td:
            home = os.path.join(td, "home")
            marker_dir = os.path.join(home, ".dispatch", "completion", "rt-fleet-clean")
            os.makedirs(marker_dir)
            for node in ("plan", "execute", "test", "report"):
                with open(os.path.join(marker_dir, "%s.json" % node), "w", encoding="utf-8") as fh:
                    json.dump({"node_id": node}, fh)
            route_file = self._write_route(td, "rt-fleet-clean")
            jobs_path = os.path.join(td, "jobs.log")
            with open(jobs_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "2026-07-19T00:00:00Z\topen\t/r\t/w\towner-clean\t"
                    "route_id=rt-fleet-clean,route_file=%s,worker_type=owner,"
                    "attempt_id=att-fleet-owner-clean,pid=999999994,pid_start=1,"
                    "attempt_schema_version=2,dispatch_depth=1,transport=headless,"
                    "execution_surface=registered-headless,registered_worker=1,"
                    "fallback_hop=same-harness-headless\n" % route_file
                )
            with mock.patch.object(dispatch.procscan, "_ps_lines", return_value=[]), \
                 mock.patch.dict(os.environ, {"AGENT_HOME": home}):
                jobs = dispatch.collect(jobs_path=jobs_path)
            owner = next(j for j in jobs if j.slug == "owner-clean")
            self.assertEqual(owner.liveness, "dead")
            self.assertIsNone(owner.note)


if __name__ == "__main__":
    unittest.main()
