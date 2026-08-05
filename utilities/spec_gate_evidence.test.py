#!/usr/bin/env python3
"""Regression tests for utilities/spec_gate_evidence.py (plan.md Phase 0 / round_1 finding 2)."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

import spec_gate_evidence as sge


def _write(path: Path, data) -> None:
    if isinstance(data, (dict, list)):
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        path.write_text(str(data), encoding="utf-8")


class SpecGateEvidenceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.project_root = self.root / "project"
        self.artifact_root = self.root / "project" / ".agent_reports"
        self.project_root.mkdir(parents=True)
        self.artifact_root.mkdir(parents=True)
        self.prd = self.artifact_root / "spec" / "prd.md"
        self.prd.parent.mkdir(parents=True)
        _write(self.prd, "# prd\n")
        self.route = self.root / "route.json"

    def _record(self, **overrides):
        record = {
            "schema_version": 2,
            "tracking": "tracked",
            "tracked_gate_evidence": {
                "workflow_mode": "tracked",
                "spec_read": {"satisfied": True, "source": "current"},
            },
            "cwd": str(self.project_root),
            "artifact_root": str(self.artifact_root),
            "route_id": "rt-fixture",
        }
        record.update(overrides)
        return record

    def _check(self, route_id="rt-fixture"):
        return sge.check(
            route_path=str(self.route),
            prd_path=str(self.prd),
            project_root=str(self.project_root),
            artifact_root=str(self.artifact_root),
            route_id=route_id,
        )

    def _bump(self, path: Path, *, ahead_of: Path | None = None):
        base = time.time()
        if ahead_of is not None:
            base = os.stat(ahead_of).st_mtime + 2
        os.utime(path, (base + 2, base + 2))

    # --- positive path -------------------------------------------------

    def test_satisfied_and_fresh_passes(self):
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        self.assertEqual(0, self._check())

    # --- negative bindings (Step 0.2) -----------------------------------

    def test_unsatisfied_fails(self):
        record = self._record()
        record["tracked_gate_evidence"]["spec_read"]["satisfied"] = False
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_untracked_fails(self):
        record = self._record(tracking="untracked")
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_workflow_mode_mismatch_fails(self):
        record = self._record()
        record["tracked_gate_evidence"]["workflow_mode"] = "untracked"
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_schema_version_mismatch_fails(self):
        record = self._record(schema_version=1)
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_route_id_mismatch_fails(self):
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check(route_id="rt-other"))

    def test_cwd_mismatch_fails(self):
        other = self.root / "elsewhere"
        other.mkdir()
        record = self._record(cwd=str(other))
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_artifact_root_mismatch_fails(self):
        other = self.root / "elsewhere-artifacts"
        other.mkdir()
        record = self._record(artifact_root=str(other))
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_stale_route_after_prd_touch_fails(self):
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        # PRD edited after the route was sealed.
        self._bump(self.prd, ahead_of=self.route)
        self.assertNotEqual(0, self._check())

    def test_malformed_json_fails(self):
        self.route.write_text("{not json", encoding="utf-8")
        self.assertNotEqual(0, self._check())

    def test_missing_route_file_fails(self):
        self.assertNotEqual(0, self._check())

    def test_relative_route_path_fails(self):
        rc = sge.check(
            route_path="route.json",
            prd_path=str(self.prd),
            project_root=str(self.project_root),
            artifact_root=str(self.artifact_root),
            route_id="rt-fixture",
        )
        self.assertNotEqual(0, rc)

    def test_non_object_json_fails(self):
        _write(self.route, [1, 2, 3])
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_missing_tracked_gate_evidence_fails(self):
        record = self._record()
        del record["tracked_gate_evidence"]
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    # --- round_1 finding 2: fail-open audit, tested and documented ------

    def test_route_id_omitted_still_requires_other_bindings(self):
        # Omitting --route-id must not become a second bypass: every other
        # binding still has to hold.
        record = self._record()
        record["tracked_gate_evidence"]["spec_read"]["satisfied"] = False
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check(route_id=""))

    def test_satisfied_record_with_omitted_route_id_denies(self):
        # dev review finding (blocking, round 2): an otherwise fully-satisfied
        # record (fresh mtime, matching cwd/artifact-root, spec_read
        # satisfied) must still DENY when the caller supplies no --route-id.
        # Before the fix, `if route_id:` skipped the comparison entirely and
        # ANY record in the same cwd/artifact-root passed with no marker.
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check(route_id=""))

    def test_satisfied_record_with_mismatched_route_id_denies(self):
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check(route_id="rt-mismatched"))

    def test_satisfied_record_with_matching_route_id_passes(self):
        _write(self.route, self._record(route_id="rt-fixture"))
        self._bump(self.route, ahead_of=self.prd)
        self.assertEqual(0, self._check(route_id="rt-fixture"))

    def test_tampered_route_content_with_forged_mtime_still_requires_bindings(self):
        # A route file assembled entirely outside the real registry (forged
        # AGENT_ROUTE_FILE) still has to satisfy every binding — forging the
        # content wins nothing by itself.
        record = self._record(cwd="/nonexistent/forged")
        _write(self.route, record)
        self._bump(self.route, ahead_of=self.prd)
        self.assertNotEqual(0, self._check())

    def test_known_fail_open_mtime_extension_documented(self):
        """Documented trust boundary (round_1 finding 2), not closable in this cycle.

        Freshness is `prd.mtime <= route.mtime` because the route record
        carries no sealed read timestamp (verified: capability-route.py never
        writes one, and adding one is a schema change to a file this cycle
        is forbidden from touching). A process with write access to the
        route file can `touch` it after editing the prd and this probe will
        still pass. This is not a new exposure: the same process could
        already forge the session-local `.spec-grounding` marker the way
        `hooks/spec-skill-gate.sh` has always trusted it, so the fall-through
        design (this probe can only ever ADD a pass path, never remove the
        marker path) keeps the worst case identical to pre-cycle behaviour.
        A real fix needs a `capability-route.py`-sealed `spec_read.read_at`
        timestamp; see dev_logs for the proposed diff and forbidden-file note.
        """
        _write(self.route, self._record())
        self._bump(self.route, ahead_of=self.prd)
        # Attacker/benign process edits the prd, then touches the route file
        # to "extend" its freshness window without a real re-read.
        self._bump(self.prd, ahead_of=self.route)
        self._bump(self.route, ahead_of=self.prd)
        self.assertEqual(0, self._check())


if __name__ == "__main__":
    unittest.main()
