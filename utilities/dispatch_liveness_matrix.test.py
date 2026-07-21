#!/usr/bin/env python3
"""Boundary/property matrix for the dispatch liveness lifecycle seam.

One harness that walks the product space where liveness bugs have historically
hidden — {lifecycle} x {pid-scope} x {timeout-sentinel} — instead of patching one
cell at a time. It targets the two coverage GAPS that let a cross-harness
``claude -p`` execute worker be abandoned ~10s after launch while its attempt row
stayed ``open`` (later surfaced as Fleet ORPHANED):

  1. the outer-subprocess deadline seam, where ``foreground_timeout <= 0`` (the
     wrapper's "wait indefinitely" sentinel) collapsed to the shortest wall;
  2. the foreground-scoped x namespace-local *executed* launch cell, which existing
     suites never drive (they force the AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN
     override back to detached).

The other axis-cells (host/namespace detection, clean-exit, marker, heartbeat,
no-progress, capacity, orphan) are already covered by dispatch_lifecycle.test.py,
dispatch_registry.test.py, stage_dispatch_*.test.py and the fleet suite; this file
does not duplicate them — it fills the untested boundary column.
"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock


def _load(mod_name, filename):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Load the lifecycle helper first so the fallback module's
# `from dispatch_lifecycle import ...` binds to the same object.
L = _load("dispatch_lifecycle", "dispatch_lifecycle.py")
F = _load("stage_dispatch_fallback", "stage-dispatch-fallback.py")

FG = L.FOREGROUND_SCOPED
DETACHED = L.DETACHED
DIRECT_TIMEOUT = 45.0  # argparse default for --direct-timeout

# The timeout-sentinel axis. `<= 0` is wait_foreground's documented "wait
# indefinitely" sentinel; the positive values are ordinary bounds; 3600 is the
# argparse default. Historically only positive values >= 1 were ever tested.
SENTINELS = [-1.0, 0.0, 1.0, 45.0, 3600.0]


class OuterDeadlineBoundaryTest(unittest.TestCase):
    """The seam that turned foreground_timeout=0 (infinite) into a 10s wall."""

    def deadline(self, ft, lifecycle):
        return F.outer_subprocess_timeout(ft, lifecycle, DIRECT_TIMEOUT)

    def test_detached_ignores_foreground_timeout(self):
        # Detached wrappers return immediately; the foreground bound is irrelevant,
        # so no sentinel value may perturb the detached spawn-confirm window.
        for ft in SENTINELS:
            self.assertEqual(self.deadline(ft, DETACHED), DIRECT_TIMEOUT, msg=f"ft={ft}")

    def test_infinite_sentinel_is_not_the_shortest_wall(self):
        # CORE REGRESSION. foreground_timeout <= 0 means "wait indefinitely" inside
        # the wrapper (wait_foreground -> proc.wait(timeout=None)). The outer
        # deadline must therefore be at least as patient as any FINITE bound — never
        # collapse to the shortest possible wall. Pre-fix: 0 -> 10s < 3610s, which
        # abandoned a just-launched cross-harness claude worker.
        finite_max = self.deadline(3600.0, FG)
        for ft in (0.0, -1.0):
            d = self.deadline(ft, FG)
            self.assertTrue(
                d is None or d >= finite_max,
                msg=(f"sentinel foreground_timeout={ft} collapsed the outer deadline "
                     f"to {d}, shorter than the finite-3600 deadline {finite_max}; a "
                     f"child that opted into 'wait indefinitely' is abandoned early."),
            )

    def test_finite_foreground_deadline_is_monotonic_and_bounded(self):
        # Ordinary positive bounds must stay finite and non-decreasing in the
        # requested timeout (the grace-margin contract), so real launches with an
        # explicit bound are never regressed by the sentinel fix.
        finite = [ft for ft in SENTINELS if ft > 0]
        deadlines = [self.deadline(ft, FG) for ft in finite]
        for ft, d in zip(finite, deadlines):
            self.assertIsNotNone(d, msg=f"finite ft={ft} must stay bounded")
            self.assertGreaterEqual(d, ft, msg=f"ft={ft}: outer deadline below inner bound")
        self.assertEqual(deadlines, sorted(deadlines), msg="non-monotonic finite deadlines")


class NamespaceLocalForegroundCellTest(unittest.TestCase):
    """foreground-scoped x namespace-local — the executed cell today's bug lived in.

    Existing coverage only drives the OVERRIDE path
    (AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 -> detached). Without the override a
    namespace-local child selects the foreground-scoped path, so wait_foreground
    runs against it — exactly the pid=29 case that was abandoned. Guard that this
    cell is real and the wait path actually reaps its child.
    """

    def test_namespace_local_selects_foreground_scoped(self):
        self.assertEqual(L.select_launch_lifecycle({}, namespace_scoped=True), FG)

    def test_wait_foreground_reaps_its_child(self):
        # A foreground-scoped launch must wait on (and reap) its child rather than
        # abandon it. Drive the real wait path with a fast child.
        child = subprocess.Popen(["sh", "-c", "exit 0"], start_new_session=True)
        outcome = L.wait_foreground(child, 5)
        self.assertEqual(outcome, L.ForegroundResult(0, ""))


class WrapperInternalWaitBoundTest(unittest.TestCase):
    """The wrapper's own foreground wait must also refuse to wait indefinitely.

    If only the outer deadline were bounded, a sentinel-0 child would run until the
    outer subprocess.run killed the whole wrapper — losing the wrapper's own
    SIGTERM->SIGKILL cleanup and clean terminal row. Clamping inside wait_foreground
    keeps the wrapper self-bounding.
    """

    def test_clamp_maps_nonpositive_to_finite_default(self):
        self.assertEqual(L.bounded_foreground_timeout(0.0), L.FOREGROUND_TIMEOUT_DEFAULT)
        self.assertEqual(L.bounded_foreground_timeout(-5.0), L.FOREGROUND_TIMEOUT_DEFAULT)
        self.assertEqual(L.bounded_foreground_timeout(120.0), 120.0)
        self.assertGreater(L.bounded_foreground_timeout(0.0), 0.0)

    def test_wait_foreground_never_waits_indefinitely_on_sentinel(self):
        proc = mock.Mock(pid=5150)
        proc.wait.return_value = 0
        L.wait_foreground(proc, 0)
        proc.wait.assert_called_once()
        self.assertEqual(
            proc.wait.call_args.kwargs.get("timeout"), L.FOREGROUND_TIMEOUT_DEFAULT
        )


if __name__ == "__main__":
    unittest.main()
