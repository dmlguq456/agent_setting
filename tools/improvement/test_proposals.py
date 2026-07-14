#!/usr/bin/env python3
"""Functional tests for the inactive proposal lifecycle."""

from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tools.improvement import proposals


class ProposalLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = mock.patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "XDG_STATE_HOME": str(self.root / "state"),
                "XDG_CONFIG_HOME": str(self.root / "config"),
                "XDG_DATA_HOME": str(self.root / "data"),
                "CLAUDE_CONFIG_DIR": str(self.root / "runtime" / "claude"),
                "CODEX_HOME": str(self.root / "runtime" / "codex"),
                "OPENCODE_CONFIG_DIR": str(self.root / "runtime" / "opencode"),
            },
            clear=False,
        )
        self.env.start()
        self.store = proposals.default_store()
        self.context = self._context("source-a", "runtime-a")
        self.context_b = self._context("source-b", "runtime-b")
        self.context_path = self._json("context.json", self.context)
        self.context_b_path = self._json("context-b.json", self.context_b)
        self.evidence = self.root / "incident.md"
        self.evidence.write_text("baseline failed\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def _context(self, source: str, runtime_version: str) -> dict:
        return {
            "source_revision": source,
            "source_dirty": False,
            "portable_fingerprint": f"portable-{source}",
            "runtimes": [
                {
                    "name": "codex",
                    "version": runtime_version,
                    "plugin": {
                        "name": "agent-harness-codex",
                        "version": "1.0.0",
                        "fingerprint": f"plugin-{source}",
                    },
                }
            ],
            "docs_fingerprint": f"docs-{runtime_version}",
            "fixture_fingerprints": [],
            "active_providers": {"skill:autopilot-code": "native-symlink"},
        }

    def _json(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def _observe(self) -> dict:
        return proposals.observe(
            self.store,
            "Runtime update conflict",
            "A generated skill and plugin cache disagree.",
            self.context_path,
            self.evidence,
        )

    def _advance_to_adopted(self) -> dict:
        record = self._observe()
        proposal_id = record["id"]
        for state in ("reproduced", "proposed"):
            record = proposals.transition(
                self.store, proposal_id, state, self.evidence
            )
        record = proposals.transition(
            self.store,
            proposal_id,
            "reviewed",
            self.evidence,
            self.context_path,
            "human:owner",
            "session:review-1",
        )
        return proposals.transition(
            self.store,
            proposal_id,
            "adopted",
            self.evidence,
            self.context_path,
            "human:owner",
            "session:adopt-1",
        )

    def test_observe_uses_xdg_state_and_copies_evidence(self) -> None:
        record = self._observe()
        self.assertEqual(record["state"], "observed")
        self.assertTrue(str(self.store).startswith(str(self.root / "state")))
        stored = self.store / record["evidence"][0]["stored_path"]
        self.assertEqual(stored.read_text(encoding="utf-8"), "baseline failed\n")
        self.assertEqual(stored.stat().st_mode & 0o777, 0o600)

    def test_read_only_list_does_not_create_store(self) -> None:
        other = self.root / "other-state" / "improvement"
        self.assertEqual(proposals.list_records(other), [])
        self.assertFalse(other.exists())

    def test_transition_requires_order_and_human_approval(self) -> None:
        record = self._observe()
        proposal_id = record["id"]
        with self.assertRaisesRegex(proposals.ProposalError, "not allowed"):
            proposals.transition(
                self.store,
                proposal_id,
                "adopted",
                self.evidence,
                self.context_path,
                "human:owner",
                "session:bad-order",
            )
        proposals.transition(self.store, proposal_id, "reproduced", self.evidence)
        proposals.transition(self.store, proposal_id, "proposed", self.evidence)
        with self.assertRaisesRegex(proposals.ProposalError, "human"):
            proposals.transition(
                self.store,
                proposal_id,
                "reviewed",
                self.evidence,
                self.context_path,
            )

    def test_stale_context_blocks_review(self) -> None:
        record = self._observe()
        proposal_id = record["id"]
        proposals.transition(self.store, proposal_id, "reproduced", self.evidence)
        proposals.transition(self.store, proposal_id, "proposed", self.evidence)
        with self.assertRaises(proposals.ProposalError) as raised:
            proposals.transition(
                self.store,
                proposal_id,
                "reviewed",
                self.evidence,
                self.context_b_path,
                "human:owner",
                "session:review-stale",
            )
        self.assertEqual(raised.exception.reason, "stale-context")
        result = proposals.check(self.store, proposal_id, self.context_b_path)
        self.assertFalse(result["fresh"])

    def test_adopted_proposal_has_version_bound_realization(self) -> None:
        record = self._advance_to_adopted()
        proposal_id = record["id"]
        record = proposals.realization(
            self.store,
            proposal_id,
            "codex",
            "active",
            "runtime-a",
            "agent-harness-codex",
            "1.0.0",
            self.context_path,
            self.evidence,
            "human:owner",
            "release:1.0.0",
        )
        self.assertEqual(record["realizations"]["codex"]["state"], "active")
        self.assertTrue(
            proposals.check(self.store, proposal_id, self.context_path, "codex")["fresh"]
        )
        self.assertFalse(
            proposals.check(self.store, proposal_id, self.context_b_path, "codex")["fresh"]
        )

    def test_runtime_update_forces_revalidation_before_reactivation(self) -> None:
        record = self._advance_to_adopted()
        proposal_id = record["id"]
        proposals.realization(
            self.store,
            proposal_id,
            "codex",
            "active",
            "runtime-a",
            "agent-harness-codex",
            "1.0.0",
            self.context_path,
            self.evidence,
            "human:owner",
            "release:1.0.0",
        )
        with self.assertRaisesRegex(proposals.ProposalError, "has not changed"):
            proposals.realization(
                self.store,
                proposal_id,
                "codex",
                "needs-revalidation",
                "runtime-a",
                "agent-harness-codex",
                "1.0.0",
                self.context_path,
                self.evidence,
            )
        proposals.realization(
            self.store,
            proposal_id,
            "codex",
            "needs-revalidation",
            "runtime-b",
            "agent-harness-codex",
            "1.1.0",
            self.context_b_path,
            self.evidence,
        )
        with self.assertRaisesRegex(proposals.ProposalError, "human"):
            proposals.realization(
                self.store,
                proposal_id,
                "codex",
                "active",
                "runtime-b",
                "agent-harness-codex",
                "1.1.0",
                self.context_b_path,
                self.evidence,
            )
        record = proposals.realization(
            self.store,
            proposal_id,
            "codex",
            "active",
            "runtime-b",
            "agent-harness-codex",
            "1.1.0",
            self.context_b_path,
            self.evidence,
            "human:owner",
            "release:1.1.0",
        )
        self.assertEqual(record["realizations"]["codex"]["runtime_version"], "runtime-b")

    def test_realization_cannot_activate_before_adoption(self) -> None:
        proposal_id = self._observe()["id"]
        with self.assertRaises(proposals.ProposalError) as raised:
            proposals.realization(
                self.store,
                proposal_id,
                "codex",
                "active",
                "runtime-a",
                "agent-harness-codex",
                "1.0.0",
                self.context_path,
                self.evidence,
                "human:owner",
                "release:early",
            )
        self.assertEqual(raised.exception.reason, "proposal-not-adopted")

    def test_protected_store_paths_are_rejected(self) -> None:
        repo_store = Path(proposals.__file__).resolve().parents[2] / ".proposal-inbox"
        with self.assertRaises(proposals.ProposalError) as repo_error:
            proposals.validate_store_path(repo_store)
        self.assertEqual(repo_error.exception.reason, "protected-store")
        runtime_store = Path(os.environ["CODEX_HOME"]) / "proposals"
        with self.assertRaises(proposals.ProposalError) as runtime_error:
            proposals.validate_store_path(runtime_store)
        self.assertEqual(runtime_error.exception.reason, "protected-store")

    def test_symlink_store_and_oversized_evidence_are_rejected(self) -> None:
        target = self.root / "target"
        target.mkdir()
        link = self.root / "store-link"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(proposals.ProposalError) as link_error:
            proposals.validate_store_path(link)
        self.assertEqual(link_error.exception.reason, "unsafe-store")

        oversized = self.root / "oversized.bin"
        with oversized.open("wb") as handle:
            handle.truncate(proposals.MAX_EVIDENCE_BYTES + 1)
        with self.assertRaises(proposals.ProposalError) as size_error:
            proposals.observe(
                self.store,
                "Oversized evidence",
                "The evidence copy must be bounded.",
                self.context_path,
                oversized,
            )
        self.assertEqual(size_error.exception.reason, "file-too-large")

    def test_context_schema_is_required(self) -> None:
        bad = self._json("bad.json", {"source_revision": "only-one-field"})
        with self.assertRaises(proposals.ProposalError) as raised:
            proposals.observe(
                self.store,
                "Bad context",
                "Incomplete fingerprints must not enter the inbox.",
                bad,
                self.evidence,
            )
        self.assertEqual(raised.exception.reason, "invalid-context")

    def test_cli_check_returns_stale_exit_code(self) -> None:
        record = self._observe()
        with redirect_stdout(io.StringIO()):
            code = proposals.main(
                [
                    "--store",
                    str(self.store),
                    "check",
                    record["id"],
                    "--context",
                    str(self.context_b_path),
                ]
            )
        self.assertEqual(code, 4)


if __name__ == "__main__":
    unittest.main()
