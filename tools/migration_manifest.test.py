#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "migration-manifest.py"
SPEC = importlib.util.spec_from_file_location("migration_manifest", TOOL)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def _make_fixture(base: Path) -> Path:
    root = base / "fixture-root"
    (root / "sub").mkdir(parents=True)
    (root / "a.txt").write_text("hello\n", encoding="utf-8")
    (root / "sub" / "b.txt").write_text(
        "old ref .claude_reports and /home/someone/project\n", encoding="utf-8"
    )
    (root / "sub" / "link.txt").symlink_to(root / "a.txt")
    try:
        os.chmod(root / "sub", 0o755)
    except OSError:
        pass
    return root


class MigrationManifestTest(unittest.TestCase):
    # regression ⑤: fixed fixture, two runs, byte-identical JSONL.
    def test_determinism_across_two_scans(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            out_a = base / "out-a"
            out_b = base / "out-b"
            for out_dir in (out_a, out_b):
                result = subprocess.run(
                    [sys.executable, str(TOOL), "scan", "--root", str(root), "--out", str(out_dir)],
                    text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            jsonl_a = (out_a / f"{root.name}.jsonl").read_bytes()
            jsonl_b = (out_b / f"{root.name}.jsonl").read_bytes()
            self.assertEqual(jsonl_a, jsonl_b)
            # run_meta carries the only timestamp -- excluding it from the
            # byte-identity check above is deliberate, not an oversight.
            meta = json.loads((out_a / "run_meta.json").read_text())
            self.assertIn("generated_at_unix", meta)

    def test_out_inside_investigated_root_is_rejected_before_scanning(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            out_dir = root / "manifest-out"
            with self.assertRaises(M.ManifestError):
                M._reject_out_inside_investigated(out_dir, root)

    def test_symlink_loop_completes_without_following(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            (root / "sub" / "loop").symlink_to(root)  # symlink back to root itself
            records, summary = M.scan_root(
                root, dest=None, do_hash=False, ref_scan_max_bytes=M.DEFAULT_REF_SCAN_MAX_BYTES,
                mirror_map={}, root_key=root.name,
            )
            self.assertTrue(summary["complete"])
            kinds = {r["path"]: r["record_type"] for r in records}
            self.assertEqual(kinds["sub/loop"], "symlink")

    def test_unreadable_directory_becomes_error_record_and_root_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                self.skipTest("root bypasses directory permission checks")
            blocked = root / "sub" / "blocked-dir"
            blocked.mkdir()
            (blocked / "hidden.txt").write_text("secret", encoding="utf-8")
            os.chmod(blocked, 0o000)
            try:
                records, summary = M.scan_root(
                    root, dest=None, do_hash=False, ref_scan_max_bytes=M.DEFAULT_REF_SCAN_MAX_BYTES,
                    mirror_map={}, root_key=root.name,
                )
            finally:
                os.chmod(blocked, 0o755)
            error_rows = [r for r in records if r["record_type"] == "error"]
            self.assertTrue(error_rows, records)
            self.assertFalse(summary["complete"])

    def test_unreadable_file_is_recorded_but_scan_still_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                self.skipTest("root bypasses file permission checks")
            blocked = root / "sub" / "blocked.txt"
            blocked.write_text("secret", encoding="utf-8")
            os.chmod(blocked, 0o000)
            try:
                records, summary = M.scan_root(
                    root, dest=None, do_hash=False, ref_scan_max_bytes=M.DEFAULT_REF_SCAN_MAX_BYTES,
                    mirror_map={}, root_key=root.name,
                )
            finally:
                os.chmod(blocked, 0o644)
            blocked_row = next(r for r in records if r["path"] == "sub/blocked.txt")
            self.assertTrue(blocked_row.get("ref_scan_skipped"))

    def test_scan_never_writes_inside_the_investigated_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            before_mtimes = {
                str(p.relative_to(root)): os.lstat(p).st_mtime_ns for p in root.rglob("*")
            }
            out_dir = base / "out"
            result = subprocess.run(
                [sys.executable, str(TOOL), "scan", "--root", str(root), "--out", str(out_dir), "--hash"],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            after_mtimes = {
                str(p.relative_to(root)): os.lstat(p).st_mtime_ns for p in root.rglob("*")
            }
            self.assertEqual(before, after)
            self.assertEqual(before_mtimes, after_mtimes)

    def test_sweep_produces_one_jsonl_per_root_plus_summary_and_run_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = _make_fixture(base)
            roots_yaml = base / "roots.yaml"
            roots_yaml.write_text(
                "roots:\n"
                f"  - key: fixture-root\n    path: {root}\n"
                f"  - key: fixture-sub\n    path: {root / 'sub'}\n",
                encoding="utf-8",
            )
            out_dir = base / "sweep-out"
            result = subprocess.run(
                [sys.executable, str(TOOL), "sweep", "--roots", str(roots_yaml), "--out", str(out_dir)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "fixture-root.jsonl").is_file())
            self.assertTrue((out_dir / "fixture-sub.jsonl").is_file())
            self.assertTrue((out_dir / "summary.md").is_file())
            self.assertTrue((out_dir / "run_meta.json").is_file())

    def test_strict_yaml_rejects_anchors_and_tags(self):
        with self.assertRaises(M.ManifestError):
            M._strict_yaml_load("roots:\n  - key: &anchor a\n    path: /tmp\n")
        with self.assertRaises(M.ManifestError):
            M._strict_yaml_load("roots: !!python/object:foo\n")

    def test_strict_yaml_parses_nested_mapping_and_sequence(self):
        text = (
            "a:\n"
            "  b: 1\n"
            "  c: two\n"
            "roots:\n"
            "  - key: x\n    path: /tmp/x\n"
            "  - key: y\n    path: /tmp/y\n"
        )
        data = M._strict_yaml_load(text)
        self.assertEqual(data["a"]["b"], "1")
        self.assertEqual(data["a"]["c"], "two")
        self.assertEqual(data["roots"], [
            {"key": "x", "path": "/tmp/x"},
            {"key": "y", "path": "/tmp/y"},
        ])

    def test_jsonl_serialization_is_compact_and_key_sorted(self):
        records = [{"record_type": "dir", "path": "a"}, {"record_type": "file", "path": "z.txt", "size": 1}]
        body = M._dump_jsonl(records)
        lines = body.splitlines()
        self.assertEqual(lines[0], '{"path":"a","record_type":"dir"}')
        self.assertEqual(lines[1], '{"path":"z.txt","record_type":"file","size":1}')

    def test_record_sort_key_orders_by_type_then_path(self):
        records = [
            {"record_type": "file", "path": "z.txt", "size": 1},
            {"record_type": "dir", "path": "a"},
            {"record_type": "symlink", "path": "m"},
        ]
        records.sort(key=lambda r: (M.RECORD_RANK[r["record_type"]], os.fsencode(r["path"])))
        self.assertEqual([r["record_type"] for r in records], ["dir", "file", "symlink"])


if __name__ == "__main__":
    unittest.main()
