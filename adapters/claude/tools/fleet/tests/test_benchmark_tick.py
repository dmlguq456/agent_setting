#!/usr/bin/env python3
"""Integrity tests for the versioned Fleet tick benchmark CLI."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS_DIR = str(Path(__file__).resolve().parents[2])
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from fleet.tests import benchmark_tick


SCRIPT = Path(benchmark_tick.__file__).resolve()
FIXTURE = SCRIPT.parent / "fixtures" / "tick_benchmark" / "v1" / "fixture.json"


def _sample(edge_builds=None, cwd_parses=6, lifecycle_parses=0):
    return {
        "wall_ns": 100,
        "cpu_ns": 90,
        "counters": {
            "raw_lifecycle_parses": lifecycle_parses,
            "raw_edge_builds_by_home": edge_builds or {"$FIXTURE_ROOT/home": 1},
            "cwd_parses": cwd_parses,
            "cache_hits": 0,
            "cache_misses": lifecycle_parses,
            "cache_evictions": 0,
            "roots_visited": 1,
            "files_visited": 1,
        },
    }


def _valid_result():
    payload = {"sessions": [], "jobs": []}
    return {
        "benchmark_schema": benchmark_tick.BENCHMARK_SCHEMA,
        "fixture_schema": benchmark_tick.FIXTURE_SCHEMA,
        "fixture_sha256": "fixture-digest",
        "iterations": 20,
        "cold_sample": _sample(lifecycle_parses=3),
        "warm_samples": [_sample() for _index in range(20)],
        "warm_summary": {
            "wall_median_ns": 100,
            "wall_p95_ns": 100,
            "cpu_median_ns": 90,
            "cpu_p95_ns": 90,
        },
        "normalized_payload": payload,
        "semantic_digest": hashlib.sha256(
            benchmark_tick._canonical_bytes(payload)
        ).hexdigest(),
        "expected": {"unique_rollouts": 6},
    }


class BenchmarkComparisonGateTest(unittest.TestCase):

    def test_invalid_cold_structural_counter_fails_comparison(self):
        baseline = _valid_result()
        for name, mutate, check in (
            (
                "edge build",
                lambda result: result["cold_sample"]["counters"][
                    "raw_edge_builds_by_home"
                ].update({"$FIXTURE_ROOT/home": 2}),
                "edge_builds_at_most_one_per_home",
            ),
            (
                "cwd parse",
                lambda result: result["cold_sample"]["counters"].update(
                    {"cwd_parses": 7}
                ),
                "cwd_parses_equal_unique_rollouts",
            ),
        ):
            with self.subTest(name=name):
                current = copy.deepcopy(baseline)
                mutate(current)
                comparison = benchmark_tick._comparison(baseline, current)
                self.assertFalse(comparison["pass"])
                self.assertFalse(comparison["checks"][check])
                self.assertTrue(
                    comparison["checks"]["unchanged_warm_lifecycle_parses_zero"]
                )


class BenchmarkComparisonCliTest(unittest.TestCase):

    def _assert_invalid_cold_counter(self, mutate, affected_check):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            result_path = root / "result.json"
            comparison_path = root / "comparison.json"
            baseline = _valid_result()
            current = copy.deepcopy(baseline)
            mutate(current)
            baseline_path.write_text(
                json.dumps(baseline, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            baseline_before = baseline_path.read_bytes()

            with mock.patch.object(
                benchmark_tick, "_hermetic_result", return_value=current
            ):
                return_code = benchmark_tick.main([
                    "--fixture",
                    str(FIXTURE),
                    "--iterations",
                    "20",
                    "--compare-baseline",
                    str(baseline_path),
                    "--result-out",
                    str(result_path),
                    "--comparison-out",
                    str(comparison_path),
                ])

            comparison = json.loads(
                comparison_path.read_text(encoding="utf-8")
            )
            self.assertEqual(return_code, 1)
            self.assertTrue(result_path.is_file())
            self.assertFalse(comparison["pass"])
            self.assertFalse(comparison["checks"][affected_check])
            self.assertEqual(baseline_path.read_bytes(), baseline_before)

    def test_main_rejects_invalid_cold_edge_build_count(self):
        self._assert_invalid_cold_counter(
            lambda result: result["cold_sample"]["counters"][
                "raw_edge_builds_by_home"
            ].update({"$FIXTURE_ROOT/home": 2}),
            "edge_builds_at_most_one_per_home",
        )

    def test_main_rejects_invalid_cold_cwd_parse_count(self):
        self._assert_invalid_cold_counter(
            lambda result: result["cold_sample"]["counters"].update(
                {"cwd_parses": 7}
            ),
            "cwd_parses_equal_unique_rollouts",
        )


class BenchmarkPathAliasCliTest(unittest.TestCase):

    def _write_baseline(self, path):
        path.write_text(
            json.dumps(_valid_result(), sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _run(self, cwd, baseline, result, comparison):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--fixture",
                str(FIXTURE),
                "--iterations",
                "20",
                "--compare-baseline",
                str(baseline),
                "--result-out",
                str(result),
                "--comparison-out",
                str(comparison),
            ],
            cwd=str(cwd),
            text=True,
            capture_output=True,
        )

    def _assert_rejected_unchanged(
        self, cwd, baseline, result, comparison, watched
    ):
        before = {path: path.read_bytes() for path in watched}
        completed = self._run(cwd, baseline, result, comparison)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must resolve to distinct paths", completed.stderr)
        self.assertEqual(
            {path: path.read_bytes() for path in watched},
            before,
        )

    def test_direct_baseline_result_and_comparison_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            other = root / "other.json"
            self._write_baseline(baseline)
            other.write_bytes(b"other sentinel\n")
            with self.subTest(alias="result"):
                self._assert_rejected_unchanged(
                    root, baseline, baseline, other, [baseline, other]
                )
            with self.subTest(alias="comparison"):
                self._assert_rejected_unchanged(
                    root, baseline, other, baseline, [baseline, other]
                )

    def test_relative_and_absolute_baseline_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            comparison = root / "comparison.json"
            self._write_baseline(baseline)
            comparison.write_bytes(b"comparison sentinel\n")
            self._assert_rejected_unchanged(
                root,
                baseline.resolve(),
                Path("baseline.json"),
                comparison,
                [baseline, comparison],
            )

    def test_symlink_and_hardlink_baseline_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            comparison = root / "comparison.json"
            self._write_baseline(baseline)
            comparison.write_bytes(b"comparison sentinel\n")
            symlink = root / "baseline-symlink.json"
            symlink.symlink_to(baseline)
            self._assert_rejected_unchanged(
                root, baseline, symlink, comparison, [baseline, comparison]
            )
            hardlink = root / "baseline-hardlink.json"
            os.link(str(baseline), str(hardlink))
            self._assert_rejected_unchanged(
                root, baseline, hardlink, comparison, [baseline, comparison]
            )

    def test_result_and_comparison_direct_and_symlink_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            output = root / "output.json"
            self._write_baseline(baseline)
            output.write_bytes(b"output sentinel\n")
            self._assert_rejected_unchanged(
                root, baseline, output, output, [baseline, output]
            )
            output_link = root / "output-symlink.json"
            output_link.symlink_to(output)
            self._assert_rejected_unchanged(
                root, baseline, output, output_link, [baseline, output]
            )


if __name__ == "__main__":
    unittest.main()
