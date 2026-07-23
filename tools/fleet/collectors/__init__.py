"""collect_all() — backbone process scan → per-harness enrichment → liveness → dispatch jobs.

Assembled incrementally: procscan is the backbone (session existence). Enrichment,
liveness, and dispatch modules are imported defensively so a partial checkout / a failing
enricher never drops backbone rows (PRD §1: enrichment fills fields; it does not decide existence).
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
    # A procscan-marked child is stronger evidence than cwd reconciliation. Once a
    # runtime child already represents a job in the same harness/cwd, do not let that
    # job's shared cwd reclassify interactive root sessions as children as well.
    represented = {
        (s.harness, os.path.realpath(s.cwd))
        for s in sessions
        if getattr(s, 'is_child', False) and getattr(s, 'cwd', None)
    }
    for s in sessions:
        if getattr(s, 'is_child', False) or getattr(s, 'app_server', False) or not getattr(s, 'cwd', None):
            continue
        for j in child_jobs:
            if s.harness != j.harness:
                continue
            if not _same_path(s.cwd, j.cwd):
                continue
            if (j.harness, os.path.realpath(j.cwd)) in represented:
                continue
            if j.parent_sid and s.session_id and j.parent_sid == s.session_id:
                continue
            if getattr(j, 'parent_cwd', None) and _same_path(s.cwd, j.parent_cwd):
                continue
            s.is_child = True
            break


def _adopt_child_titles(sessions, jobs):
    """Atomically associate title and NOW from one exact child."""
    children = [s for s in sessions if getattr(s, 'is_child', False)]
    by_identity = {}
    by_session_id = {}
    by_cwd = {}
    for child in children:
        identity = (getattr(child, 'harness', None), getattr(child, 'pid', None),
                    getattr(child, 'proc_start', None))
        if all(item is not None for item in identity):
            by_identity.setdefault(identity, []).append(child)
        if child.harness and child.session_id:
            by_session_id.setdefault((child.harness, child.session_id), []).append(child)
        if child.cwd and child.harness:
            by_cwd.setdefault((child.harness, os.path.realpath(child.cwd)), []).append(child)
    for job in jobs:
        source = None
        ambiguity = None
        identity = (getattr(job, 'harness', None), getattr(job, 'pid', None),
                    getattr(job, 'proc_start', None))
        if all(item is not None for item in identity):
            candidates = by_identity.get(identity, [])
            if len(candidates) == 1:
                source = candidates[0]
            elif len(candidates) > 1:
                ambiguity = "multiple-child-identity-candidates"
        runtime_sid = getattr(job, '_runtime_session_id', None)
        if source is None and ambiguity is None and runtime_sid and getattr(job, 'harness', None):
            candidates = by_session_id.get((job.harness, runtime_sid), [])
            if len(candidates) == 1:
                source = candidates[0]
            elif len(candidates) > 1:
                ambiguity = "multiple-child-session-id-candidates"
        has_exact_binding = all(item is not None for item in identity) or bool(runtime_sid)
        if (source is None and ambiguity is None and not has_exact_binding
                and getattr(job, 'cwd', None) and getattr(job, 'harness', None)):
            candidates = by_cwd.get((job.harness, os.path.realpath(job.cwd)), [])
            if len(candidates) == 1:
                source = candidates[0]
            elif len(candidates) > 1:
                ambiguity = "multiple-child-cwd-candidates"
        if source is None:
            if ambiguity:
                job.association_ambiguity = ambiguity
                job.summary = None
            continue
        # Values cross the boundary as one association decision. Dispatch context
        # is intentionally absent: headless runtimes expose no session-owned window.
        if not getattr(job, 'title', None):
            job.title = getattr(source, 'title', None)
        job.summary = getattr(source, 'summary', None)


def collect_all(harness_filter=None, jobs_path=None):
    """Return (sessions, jobs).

    harness_filter: optional iterable of harness names (fleet + dispatch both honor it).
    jobs_path:      override for .dispatch/jobs.log (else env / default).
    """
    sessions = procscan.scan(harness_filter=harness_filter)

    # --- per-harness passive enrichment (each enricher self-resolves its home from env) ---
    enrichers = {}
    modules = {}
    for name in ("claude", "codex", "opencode"):
        try:
            mod = importlib.import_module("." + name, __package__)
            modules[name] = mod
            enrichers[name] = mod.enrich
        except Exception:
            pass
    # Reserve strong process-owned identities before any PID-ordered fallback.
    # Codex uses this to prevent one same-cwd rollout from labeling two TUIs.
    try:
        prepare = getattr(modules.get("codex"), "prepare_tick", None)
        if prepare:
            prepare(sessions)
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
                    if isinstance(cu, dict):
                        if cu.get("rl_5h") is not None:
                            s.rl_5h = cu["rl_5h"]
                        if cu.get("rl_7d") is not None:
                            s.rl_7d = cu["rl_7d"]
                        if cu.get("windows"):
                            s.rl_windows = cu["windows"]
                        if cu.get("rs_5h") or cu.get("rs_7d"):
                            s.rl_rs = (cu.get("rs_5h"), cu.get("rs_7d"))
                    else:
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

    try:
        from ..projection import normalize_context, _evidence
        now = _time.time()
        for session in sessions:
            session.context, session._context_evidence = normalize_context(
                _evidence(session), now=now)
    except Exception:
        pass

    try:
        _adopt_child_titles(sessions, jobs)
    except Exception:
        pass

    # v16: all surfaces receive one projection after evidence collection and association.
    try:
        from ..projection import attach_projections
        # F-28a's terminal-row node evidence (dispatch.py's _scan_route_nodes) is the only
        # place a route node's `done`/`failed` state survives once its live job has already
        # gone terminal — thread it through so the projection never regresses to "pending"
        # for a node the registry already resolved.
        attach_projections(sessions, jobs, artifact_root=os.environ.get("AGENT_ARTIFACT_ROOT"),
                           now=_time.time(),
                           node_evidence=getattr(dispatch.collect, "last_route_nodes", None))
    except Exception:
        # Projection failure is fail-closed at the row boundary, never a reason to drop data.
        from ..model import WorkProjection
        for entity in sessions + jobs:
            if getattr(entity, "work_projection", None) is None:
                entity.work_projection = WorkProjection(source="none", ambiguity="projection-error")

    # F-25: drop cross-tick hysteresis entries for rows that no longer exist. Runs after
    # BOTH sessions and jobs are classified — sweeping earlier would evict live job keys.
    try:
        from .. import model
        model.tracker_sweep()
    except Exception:
        pass

    return sessions, jobs
