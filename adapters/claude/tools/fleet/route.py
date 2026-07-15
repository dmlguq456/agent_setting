"""Route record consumption (F-28a, prd.md:302) — read-only, tolerant.

`route.py` is the sibling of `model.py`: `model` owns the cross-harness Session/DispatchJob
schema + F-25 classifier, `route` owns immutable stage-dispatch route-record parsing, its DAG,
and per-route view assembly. Both `render.py` (F-28b breadcrumb, F-30 process view) and
`fleet.py` (`--json route`) need this — it is not collector-only — so it lives at the package
root next to `model.py`, not under `collectors/`.

Zero-dep stdlib only. **NEVER writes** — this module contains no file-write call of any kind
(no write-mode file open, no path-replace, no stream-write method call). The read-only invariant
(prd.md:287) is enforced by a static grep gate (plan §7 G3), not just by convention — see
`_internal/dev_reviews/` for the exact pattern the gate checks.

Contract:
  load(path, expect_hash=None, expect_id=None)  -> record dict | None, never raises.
  route_hash(record)                             -> "sha256:..." (utilities/capability-route.py
                                                     :21-26 reproduced verbatim, P1).
  node_order(record)                             -> [[node_id, ...], ...] Kahn levels.
  resolve_records(jobs, node_evidence=None)      -> {route_id: record} — the ONE impure entry
                                                     point (calls load() per distinct route_file
                                                     seen on a live job OR in terminal-row
                                                     evidence — a route with no live job left
                                                     still resolves via node_evidence).
  build_views(jobs, node_evidence, records, now) -> [view, ...] — PURE (no I/O, no clock read);
                                                     `now` is always an argument, never sampled
                                                     internally, so it is hermetically testable.
  collect_views(jobs, node_evidence, now=None)   -> [view, ...] — convenience wrapper:
                                                     resolve_records() + build_views().
  summary(views)                                 -> --json-shaped list (drops internal refs).
  clear_cache()                                  -> test hermeticity (model.reset_state_tracker
                                                     precedent).
"""
import hashlib
import json
import os
import time

_CACHE = {}   # {abspath: (mtime, size, record|None)}


# --- hashing (P1 — utilities/capability-route.py:21-26, reproduced exactly) ---
def _canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def route_hash(record):
    bare = {k: v for k, v in record.items() if k not in ("route_hash", "route_id")}
    return "sha256:" + hashlib.sha256(_canonical(bare)).hexdigest()


def clear_cache():
    """Test hermeticity: drop the mtime+size cache (model.reset_state_tracker() precedent)."""
    _CACHE.clear()


def _load_uncached(abspath):
    try:
        with open(abspath, encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    if record.get("schema_version") != 1:
        return None   # future schema — do not guess-interpret (prd.md:481 sync obligation)
    digest = record.get("route_hash")
    if not isinstance(digest, str):
        return None
    try:
        if digest != route_hash(record):
            return None
    except Exception:
        return None
    expected_id = ("rt-" + digest.split(":", 1)[1][:16]) if digest.startswith("sha256:") else None
    if record.get("route_id") != expected_id:
        return None
    nodes = record.get("nodes")
    if not isinstance(nodes, list):
        return None
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str):
            return None
    return record


def load(path, expect_hash=None, expect_id=None):
    """record dict | None. Never raises — any failure (missing file, bad json, hash mismatch,
    future schema, malformed nodes[], pipe/record mismatch) is a quiet None → caller falls back
    to the existing pipe heuristic (F-28 v8 contract, unchanged)."""
    if not path or not isinstance(path, (str, bytes, os.PathLike)):
        return None   # I2: a non-path-like value (int/dict/list/...) is a caller bug, not a
                       # crash — a pipe field is always text, so this can only happen via a
                       # malformed caller, and "never raises" wins over surfacing that loudly.
    try:
        abspath = os.path.abspath(path)
        st = os.stat(abspath)
        key = (st.st_mtime, st.st_size)
    except (OSError, TypeError, ValueError):
        return None
    cached = _CACHE.get(abspath)
    if cached is not None and (cached[0], cached[1]) == key:
        record = cached[2]
    else:
        record = _load_uncached(abspath)
        _CACHE[abspath] = (key[0], key[1], record)
    if record is None:
        return None
    if expect_hash is not None and record.get("route_hash") != expect_hash:
        return None
    if expect_id is not None and record.get("route_id") != expect_id:
        return None
    return record


# --- DAG (Step 2/3 shared source) ---
def node_order(record):
    """[[node_id, ...], ...] — Kahn levels. Same-level order = record's `nodes[]` original
    order (the compiler's order, not sorted — deterministic across ticks). A cycle or an
    unresolvable `depends_on` reference never raises: the unresolved remainder is placed as one
    final level, in original order (tolerant — a slightly-off render beats a crash, plan §3.1)."""
    nodes = (record or {}).get("nodes") or []
    ids = [n.get("id") for n in nodes if isinstance(n, dict) and isinstance(n.get("id"), str)]
    id_set = set(ids)
    deps = {}
    for n in nodes:
        nid = n.get("id")
        if nid in id_set:
            deps[nid] = [x for x in (n.get("depends_on") or []) if isinstance(x, str)]
    remaining = list(ids)
    placed = set()
    levels = []
    while remaining:
        ready = [nid for nid in remaining
                 if all((d in placed) or (d not in id_set) for d in deps.get(nid, []))]
        if not ready:
            levels.append(remaining)   # cycle/unresolved remainder — dump as-is, tolerant
            break
        levels.append(ready)
        placed.update(ready)
        remaining = [nid for nid in remaining if nid not in placed]
    return levels


# --- node state (§3.3 single source — Step 2 breadcrumb AND Step 3 card both call this) ---
def _node_state(node_id, route_jobs, ev_by_node, now):
    """One node's state, per the priority table (plan §3.3): active (live job) beats failed
    (dead/stale live job, or a killed/cancelled/fail-noted registry row) beats done (a clean
    registry row) beats pending (no evidence at all). `now` is the ONLY clock input — never
    read internally, so this stays hermetically testable (T1-14/T1-15)."""
    live = [j for j in route_jobs if getattr(j, "route_node", None) == node_id]
    active = [j for j in live if j.liveness == "working"]
    if active:
        j = active[0]
        return {"state": "active", "elapsed_min": j.elapsed_min, "model": j.model,
                "harness": j.harness, "effort": j.effort, "pid": j.pid, "note": None, "job": j}
    failed_live = [j for j in live if j.liveness in ("stale", "dead")]
    ev = ev_by_node.get(node_id) or {}
    note = ev.get("note")
    fail_note = bool(note) and (str(note).startswith("fleet-kill") or str(note).startswith("dead-"))
    ev_status = ev.get("status")
    if failed_live or ev_status in ("killed", "cancelled") or (ev_status == "done" and fail_note):
        if failed_live:
            j = failed_live[0]
            return {"state": "failed", "elapsed_min": j.elapsed_min, "model": j.model,
                    "harness": j.harness, "effort": j.effort, "pid": j.pid,
                    "note": note, "job": j}
        return {"state": "failed", "elapsed_min": _ev_elapsed(ev, now), "model": ev.get("model"),
                "harness": ev.get("harness"), "effort": ev.get("effort"), "pid": ev.get("pid"),
                "note": note, "job": None}
    if ev_status == "done":
        return {"state": "done", "elapsed_min": _ev_elapsed(ev, now), "model": ev.get("model"),
                "harness": ev.get("harness"), "effort": ev.get("effort"), "pid": ev.get("pid"),
                "note": note, "job": None}
    return {"state": "pending", "elapsed_min": None, "model": None, "harness": None,
            "effort": None, "pid": None, "note": None, "job": None}


def _ev_elapsed(ev, now):
    ts = ev.get("ts")
    if ts is None:
        return ev.get("elapsed_min")
    try:
        return max(0, int((now - ts) / 60))
    except Exception:
        return ev.get("elapsed_min")


def _heuristic_view(route_id, route_jobs):
    """A route_id is known (from the pipe) but the record itself never loaded (hash mismatch /
    file gone / future schema). No DAG is available — the degrade card (§5.3) falls back to the
    existing `_PIPE_STAGES` breadcrumb instead of this view's (empty) node list."""
    return {"route_id": route_id, "route_hash": None, "source": "heuristic",
            "capability": None, "capability_mode": None, "execution_topology": None,
            "effective_intensity": None, "progress": {"done": 0, "total": 0},
            "nodes": [], "key": route_id}


def _record_view(record, route_id, route_jobs, ev_by_node, now):
    levels = node_order(record)
    node_by_id = {n["id"]: n for n in (record.get("nodes") or [])
                  if isinstance(n, dict) and isinstance(n.get("id"), str)}
    nodes = []
    done = 0
    for level_i, level in enumerate(levels):
        for nid in level:
            rn = node_by_id.get(nid, {})
            st = _node_state(nid, route_jobs, ev_by_node, now)
            if st["state"] == "done":
                done += 1
            nodes.append({
                "id": nid, "depends_on": list(rn.get("depends_on") or []), "level": level_i,
                "state": st["state"], "gate": rn.get("completion_gate"), "note": st["note"],
                "elapsed_min": st["elapsed_min"], "model": st["model"], "harness": st["harness"],
                "effort": st["effort"], "pid": st["pid"], "job": st["job"],
            })
    return {"route_id": route_id, "route_hash": record.get("route_hash"), "source": "record",
            "capability": record.get("capability"), "capability_mode": record.get("capability_mode"),
            "execution_topology": record.get("execution_topology"),
            "effective_intensity": record.get("effective_intensity"),
            "progress": {"done": done, "total": len(nodes)}, "nodes": nodes, "key": route_id}


def build_views(jobs, node_evidence, records, now):
    """PURE — jobs/node_evidence/records/now are the entire input; no file I/O, no clock read.
    One view per distinct route_id referenced by `jobs` (via job.route_id); a job without a
    route_id contributes nothing (prd.md:302 — record-less jobs keep the existing breadcrumb,
    they never enter the route summary)."""
    node_evidence = node_evidence or {}
    records = records or {}
    by_route = {}
    order = []
    for j in jobs:
        rid = getattr(j, "route_id", None)
        if not rid:
            continue
        if rid not in by_route:
            by_route[rid] = []
            order.append(rid)
        by_route[rid].append(j)
    # A route with no LIVE job (every node done/failed, or a hermetic test exercising
    # evidence/records directly — T1-15/pending-only cases) still gets a view as long as a
    # record or terminal evidence names it — a route does not stop existing just because
    # nothing about it is currently running.
    for rid in list(records) + list(node_evidence):
        if rid not in by_route:
            by_route[rid] = []
            order.append(rid)
    views = []
    for rid in order:
        route_jobs = by_route[rid]
        record = (records or {}).get(rid)
        if record is None:
            views.append(_heuristic_view(rid, route_jobs))
        else:
            views.append(_record_view(record, rid, route_jobs, node_evidence.get(rid) or {}, now))
    return views


def resolve_records(jobs, node_evidence=None):
    """The one impure entry point: calls load() once per distinct (route_file, route_id,
    route_hash) tuple seen across `jobs` ∪ `node_evidence` (code-test verification.md §10 — a
    route whose every carrying job has already finished has NO live job left to carry
    route_file; `node_evidence` — `_scan_route_nodes`'s terminal-row pass — is the only
    remaining place that path survives). Best-effort — a job with route_id but no route_file
    (proc jobs never export AGENT_ROUTE_HASH — §3.2.2) still gets a load() attempt with
    expect_hash=None; a failed load simply omits that route_id from the result (build_views
    then produces a heuristic view instead of raising)."""
    records = {}
    seen = set()
    for j in jobs:
        rid = getattr(j, "route_id", None)
        rf = getattr(j, "route_file", None)
        if not rid or not rf or rid in records:
            continue
        rh = getattr(j, "route_hash", None)
        cache_key = (rf, rid, rh)
        if cache_key in seen:
            continue
        seen.add(cache_key)
        rec = load(rf, expect_hash=rh, expect_id=rid)
        if rec is not None:
            records[rid] = rec
    # ★ code-test verification.md §10 fix — jobs alone under-covers a route whose surviving
    # trace is entirely terminal (registry) evidence: every node's row is `done`/`killed`/
    # `cancelled`, so `_scan_jobs_log` dropped all of them before this function ever sees a
    # job for that route_id (the same "terminal rows vanish before classification" gap
    # `_scan_route_nodes` exists to patch for NODE STATE — this patches it for RECORD LOOKUP).
    # Any one node's evidence carrying `route_file` is enough; they all point at the same file.
    for rid, nodes in (node_evidence or {}).items():
        if rid in records:
            continue
        for node_ev in (nodes or {}).values():
            rf = (node_ev or {}).get("route_file")
            if not rf:
                continue
            rh = (node_ev or {}).get("route_hash")
            cache_key = (rf, rid, rh)
            if cache_key in seen:
                continue
            seen.add(cache_key)
            rec = load(rf, expect_hash=rh, expect_id=rid)
            if rec is not None:
                records[rid] = rec
                break
    return records


def collect_views(jobs, node_evidence=None, now=None):
    """Convenience wrapper used by fleet.py/render.py: resolve_records() (impure) + build_views
    (pure). `now` defaults to time.time() here — the ONLY place in this module that reads the
    clock — so build_views itself never needs to."""
    now = time.time() if now is None else now
    node_evidence = node_evidence or {}
    records = resolve_records(jobs, node_evidence)
    return build_views(jobs, node_evidence, records, now)


def summary(views):
    """--json `route` key shape (prd.md:302 — "요약: capability/topology/nodes 진행/route_id").
    Drops internal fields (`job` object refs, `key`) that never belong in a JSON snapshot.
    A view with no route_id is never emitted (§3.4 — no empty-key ghost entries)."""
    out = []
    for v in views:
        if not v.get("route_id"):
            continue
        nodes = [{"id": n["id"], "depends_on": n.get("depends_on") or [], "level": n.get("level"),
                  "state": n.get("state"), "gate": n.get("gate"), "note": n.get("note"),
                  "elapsed_min": n.get("elapsed_min"), "model": n.get("model"),
                  "harness": n.get("harness"), "effort": n.get("effort")}
                 for n in v.get("nodes") or []]
        out.append({"route_id": v.get("route_id"), "route_hash": v.get("route_hash"),
                    "source": v.get("source"), "capability": v.get("capability"),
                    "capability_mode": v.get("capability_mode"),
                    "execution_topology": v.get("execution_topology"),
                    "effective_intensity": v.get("effective_intensity"),
                    "progress": v.get("progress") or {"done": 0, "total": 0}, "nodes": nodes})
    return out
