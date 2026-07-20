#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "utilities" / "worktree-cleanup.py"


def run(argv: list[str], cwd: Path | None = None, check: bool = True):
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"{argv}: {result.stdout}\n{result.stderr}")
    return result


class CleanupFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "project"
        self.wt_root = self.root / "project-wt"
        self.jobs = self.root / "jobs.log"
        self.audit = self.root / "cleanup.jsonl"
        run(["git", "init", "--bare", "-q", str(self.remote)])
        run(["git", "clone", "-q", str(self.remote), str(self.repo)])
        run(["git", "-C", str(self.repo), "config", "user.name", "test"])
        run(["git", "-C", str(self.repo), "config", "user.email", "test@example.com"])
        (self.repo / "source.txt").write_text("base\n", encoding="utf-8")
        run(["git", "-C", str(self.repo), "add", "source.txt"])
        run(["git", "-C", str(self.repo), "commit", "-qm", "base"])
        run(["git", "-C", str(self.repo), "branch", "-M", "main"])
        run(["git", "-C", str(self.repo), "push", "-qu", "origin", "main"])
        run(["git", "--git-dir", str(self.remote), "symbolic-ref", "HEAD", "refs/heads/main"])

    def close(self):
        self.temp.cleanup()

    def add_worktree(self, name: str, with_commit: bool = False) -> Path:
        path = self.wt_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "-C", str(self.repo), "worktree", "add", "-q", "-b", name, str(path), "main"])
        if with_commit:
            (path / f"{name}.txt").write_text(f"{name}\n", encoding="utf-8")
            run(["git", "-C", str(path), "add", "."])
            run(["git", "-C", str(path), "commit", "-qm", name])
        return path

    def merge_and_push(self, name: str):
        run(["git", "-C", str(self.repo), "merge", "--no-ff", "-qm", f"merge {name}", name])
        run(["git", "-C", str(self.repo), "push", "-q", "origin", "main"])

    def cleanup(self, path: Path, apply: bool = False):
        action = "--apply" if apply else "--check"
        return run(
            [
                str(SCRIPT),
                action,
                "--worktree",
                str(path),
                "--integration-ref",
                "main",
                "--jobs",
                str(self.jobs),
                "--audit",
                str(self.audit),
            ],
            cwd=self.root,
            check=False,
        )

    def cleanup_all(self, apply: bool = False):
        action = "--apply" if apply else "--check"
        return run(
            [
                str(SCRIPT),
                action,
                "--all-eligible",
                "--repo",
                str(self.repo),
                "--integration-ref",
                "main",
                "--jobs",
                str(self.jobs),
                "--audit",
                str(self.audit),
            ],
            cwd=self.root,
            check=False,
        )


class WorktreeCleanupTests(unittest.TestCase):
    def setUp(self):
        self.fx = CleanupFixture()

    def tearDown(self):
        self.fx.close()

    def test_eligible_removes_worktree_preserves_branch_and_reconciles(self):
        path = self.fx.add_worktree("eligible", with_commit=True)
        self.fx.merge_and_push("eligible")
        self.fx.jobs.write_text(
            f"2026-07-14T00:00:00Z\topen\t{path}\t{path}\teligible\t"
            "attempt_schema_version=2,attempt_id=att-cleanup-current,"
            "dispatch_depth=1,transport=headless,execution_surface=registered-headless,"
            "registered_worker=1,fallback_hop=same-harness-headless,"
            "capability=autopilot-code,harness=codex\n"
            f"2026-07-14T00:00:01Z\topen\t{path}\t{path}\teligible-legacy\t"
            "capability=autopilot-code,harness=codex,depth=1\n",
            encoding="utf-8",
        )
        checked = self.fx.cleanup(path)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("status=eligible", checked.stdout)
        applied = self.fx.cleanup(path, apply=True)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertIn("status=removed", applied.stdout)
        self.assertFalse(path.exists())
        branch = run(
            ["git", "-C", str(self.fx.repo), "show-ref", "--verify", "refs/heads/eligible"],
            check=False,
        )
        self.assertEqual(branch.returncode, 0)
        registry = self.fx.jobs.read_text(encoding="utf-8")
        current = next(line for line in registry.splitlines() if "att-cleanup-current" in line)
        legacy = next(line for line in registry.splitlines() if "eligible-legacy" in line)
        self.assertIn("\tdone\t", current)
        self.assertIn("note=cleanup-merged", current)
        self.assertIn("\topen\t", legacy)
        self.assertNotIn("note=cleanup-merged", legacy)
        self.assertIn('"artifact_harvest_required": false', self.fx.audit.read_text())

    def test_dirty_is_blocked(self):
        path = self.fx.add_worktree("dirty")
        (path / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        result = self.fx.cleanup(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("dirty", result.stdout)
        self.assertTrue(path.exists())

    def test_unmerged_is_blocked(self):
        path = self.fx.add_worktree("unmerged", with_commit=True)
        result = self.fx.cleanup(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("unmerged", result.stdout)

    def test_locked_is_blocked(self):
        path = self.fx.add_worktree("locked")
        run(["git", "-C", str(self.fx.repo), "worktree", "lock", str(path)])
        result = self.fx.cleanup(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("locked", result.stdout)

    def test_active_process_is_blocked(self):
        path = self.fx.add_worktree("active")
        proc = subprocess.Popen(["sh", "-c", "while :; do sleep 1; done"], cwd=path)
        try:
            time.sleep(0.1)
            result = self.fx.cleanup(path)
            self.assertEqual(result.returncode, 3)
            self.assertIn("active-process", result.stdout)
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_integration_not_pushed_is_blocked(self):
        path = self.fx.add_worktree("push-pending")
        run(["git", "-C", str(self.fx.repo), "commit", "--allow-empty", "-qm", "local main"])
        result = self.fx.cleanup(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("integration-not-pushed", result.stdout)

    def test_missing_integration_upstream_is_blocked(self):
        path = self.fx.add_worktree("no-upstream")
        run(["git", "-C", str(self.fx.repo), "branch", "--unset-upstream", "main"])
        result = self.fx.cleanup(path)
        self.assertEqual(result.returncode, 3)
        self.assertIn("integration-upstream-missing", result.stdout)

    def test_primary_is_blocked(self):
        result = self.fx.cleanup(self.fx.repo)
        self.assertEqual(result.returncode, 3)
        self.assertIn("primary-worktree", result.stdout)

    def test_all_eligible_only_considers_job_registry_worktrees(self):
        registered = self.fx.add_worktree("registered")
        unrelated = self.fx.add_worktree("unrelated")
        self.fx.jobs.write_text(
            f"2026-07-14T00:00:00Z\tdone\t{self.fx.repo}\t{registered}\t"
            "registered\tattempt_schema_version=2,attempt_id=att-cleanup-all,"
            "dispatch_depth=1,transport=headless,"
            "execution_surface=registered-headless,registered_worker=1,"
            "fallback_hop=same-harness-headless,"
            "capability=autopilot-code,harness=codex\n",
            encoding="utf-8",
        )
        result = self.fx.cleanup_all(apply=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(registered.exists())
        self.assertTrue(unrelated.exists())

    def test_all_eligible_legacy_row_cannot_authorize_removal(self):
        registered = self.fx.add_worktree("legacy-only")
        self.fx.jobs.write_text(
            f"2026-07-14T00:00:00Z\tdone\t{self.fx.repo}\t{registered}\t"
            "legacy-only\tcapability=autopilot-code,harness=codex,depth=1\n",
            encoding="utf-8",
        )
        result = self.fx.cleanup_all(apply=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("status=no-candidates", result.stdout)
        self.assertTrue(registered.exists())

    def test_all_eligible_current_axes_without_attempt_cannot_authorize_removal(self):
        registered = self.fx.add_worktree("attemptless")
        self.fx.jobs.write_text(
            f"2026-07-14T00:00:00Z\tdone\t{self.fx.repo}\t{registered}\t"
            "attemptless\tattempt_schema_version=2,dispatch_depth=1,"
            "transport=headless,execution_surface=registered-headless,"
            "registered_worker=1,fallback_hop=same-harness-headless\n",
            encoding="utf-8",
        )
        result = self.fx.cleanup_all(apply=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("status=no-candidates", result.stdout)
        self.assertTrue(registered.exists())


if __name__ == "__main__":
    unittest.main()
