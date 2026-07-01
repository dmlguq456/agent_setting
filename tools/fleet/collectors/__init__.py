"""collect_all() — backbone process scan → per-harness enrichment → liveness → dispatch jobs.

Assembled incrementally: procscan is the backbone (session existence). Enrichment,
liveness, and dispatch modules are imported defensively so a partial checkout / a failing
enricher never drops the backbone rows (PRD §1: enrichment is 칸 채우기, not 존재 판정).
"""
import importlib
import time as _time

from . import procscan


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

    return sessions, jobs
