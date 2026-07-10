"""collect_all() — backbone process scan → per-harness enrichment → liveness → dispatch jobs.

Assembled incrementally: procscan is the backbone (session existence). Enrichment,
liveness, and dispatch modules are imported defensively so a partial checkout / a failing
enricher never drops the backbone rows (PRD §1: enrichment is 칸 채우기, not 존재 판정).
"""
import importlib
import os
import time as _time

from . import procscan


def _same_path(a, b):
    if not a or not b:
        return False
    return a == b or os.path.realpath(a) == os.path.realpath(b)


def _mark_dispatch_child_sessions(sessions, jobs):
    """Hide runtime session rows that are already represented by dispatch jobs.

    Claude exposes an env marker for child sessions at procscan time, but Codex/OpenCode
    headless runs only become identifiable after jobs.log is collected. Match active child
    jobs by runtime+cold cwd, while explicitly protecting the parent session cwd/id.
    """
    child_jobs = []
    for j in jobs:
        if not getattr(j, 'cwd', None) or not getattr(j, 'harness', None):
            continue
        if not (getattr(j, 'is_child', False) or getattr(j, 'parent_sid', None)
                or getattr(j, 'parent_cwd', None) or getattr(j, 'parent_slug', None)):
            continue
        child_jobs.append(j)
    if not child_jobs:
        return
    for s in sessions:
        if getattr(s, 'is_child', False) or getattr(s, 'app_server', False) or not getattr(s, 'cwd', None):
            continue
        for j in child_jobs:
            if s.harness != j.harness:
                continue
            if not _same_path(s.cwd, j.cwd):
                continue
            if j.parent_sid and s.session_id and j.parent_sid == s.session_id:
                continue
            if getattr(j, 'parent_cwd', None) and _same_path(s.cwd, j.parent_cwd):
                continue
            s.is_child = True
            break


def collect_all(harness_filter=None, jobs_path=None):
    """Return (sessions, jobs).

    harness_filter: optional iterable of harness names (fleet + dispatch both honor it).
    jobs_path:      override for .dispatch/jobs.log (else env / default).
    """
    sessions = procscan.scan(harness_filter=harness_filter)

    # --- per-harness passive enrichment (each enricher self-resolves its home from env) ---
    enrichers = {}
    for name in ("claude", "codex", "opencode"):
        try:
            mod = importlib.import_module("." + name, __package__)
            enrichers[name] = mod.enrich
        except Exception:
            pass
    for s in sessions:
        fn = enrichers.get(s.harness)
        if fn:
            try:
                fn(s)
            except Exception:
                pass  # enrichment failure never removes the backbone row

    # --- account usage via the oauth API (authoritative; taps lag / lack per-model buckets) ---
    # Overrides every claude session's rate fields with the account-shared values so the render
    # layer's freshest-pick sees them; on any failure the tap values simply remain (fallback).
    try:
        from . import usage_api
        au = usage_api.account_usage()
        if au:
            for s in sessions:
                if s.harness == "claude" and not s.is_child:
                    if au["rl_5h"] is not None:
                        s.rl_5h = au["rl_5h"]
                    if au["rl_7d"] is not None:
                        s.rl_7d = au["rl_7d"]
                    if au["rl_ms"]:
                        s.rl_ms = au["rl_ms"]
                    if au.get("rs_5h") or au.get("rs_7d"):
                        s.rl_rs = (au.get("rs_5h"), au.get("rs_7d"))
    except Exception:
        pass

    # --- codex account usage from the newest rollout on disk (account-shared) — keeps the codex
    # usage row alive/correct even when only app-servers (no rollout) are running.
    try:
        from . import codex as _codex
        cu = _codex.account_usage()
        if cu:
            for s in sessions:
                if s.harness == "codex":
                    if cu[0] is not None:
                        s.rl_5h = cu[0]
                    if cu[1] is not None:
                        s.rl_7d = cu[1]
                    if len(cu) > 3 and (cu[2] or cu[3]):
                        s.rl_rs = (cu[2], cu[3])
    except Exception:
        pass

    # --- liveness → 4-state ---
    try:
        from . import liveness
        now = _time.time()
        for s in sessions:
            s.liveness = liveness.classify(s, now)
    except Exception:
        pass

    # --- dispatch section ---
    jobs = []
    try:
        from . import dispatch
        jobs = dispatch.collect(jobs_path=jobs_path, harness_filter=harness_filter)
    except Exception:
        jobs = []

    try:
        _mark_dispatch_child_sessions(sessions, jobs)
    except Exception:
        pass

    return sessions, jobs
