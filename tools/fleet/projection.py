"""Single fail-closed work/context projection for Fleet.

This module is deliberately source-agnostic: collectors supply already observed
entities and route evidence, while every display and JSON surface consumes the
result.  It never starts a provider and never writes harness state.
"""

from __future__ import annotations

import glob
import os
import time
from typing import Iterable, Optional

from .model import (
    ActiveNodeProjection,
    ContextEvidence,
    ContextProjection,
    DispatchJob,
    ProgressProjection,
    Session,
    WorkProjection,
)
from .token_budget import policy_band


ROUTE_RECORD_MISMATCH = "route-record-mismatch"
MULTIPLE_LEAF_CANDIDATES = "multiple-leaf-candidates"
MULTIPLE_CHILD_CWD_CANDIDATES = "multiple-child-cwd-candidates"
MULTIPLE_OWNER_ROUTES = "multiple-owner-routes"
OWNER_ROUTE_CONFLICT = "owner-route-conflict"
MULTIPLE_ARTIFACT_PLAN_DIRS = "multiple-artifact-plan-dirs"


def _realpath(value):
    return os.path.realpath(value) if value else ""


def _field(entity, name, default=None):
    if isinstance(entity, dict):
        return entity.get(name, default)
    return getattr(entity, name, default)


def _evidence(entity):
    value = _field(entity, "_context_evidence")
    if isinstance(value, ContextEvidence):
        return value
    if not isinstance(value, dict):
        pct = _field(entity, "ctx_pct")
        return ContextEvidence(used_pct=pct, source="legacy" if pct is not None else "unknown")
    return ContextEvidence(
        used_pct=value.get("used_pct"), source=value.get("source", "unknown"),
        sequence=value.get("sequence"), source_head_sequence=value.get("source_head_sequence"),
        observed_at=value.get("observed_at"), fresh_until=value.get("fresh_until"),
        invalid_reason=value.get("invalid_reason"),
    )


def normalize_context(evidence, now=None):
    """Return ``(public, private)`` context values with exact ordering/freshness checks."""
    now = time.time() if now is None else now
    ev = evidence if isinstance(evidence, ContextEvidence) else _evidence({"_context_evidence": evidence})
    reason = ev.invalid_reason
    pct = ev.used_pct
    if reason is None and not isinstance(pct, (int, float)):
        reason = "missing-context"
    if reason is None and (isinstance(pct, bool) or pct < 0 or pct > 100):
        reason = "malformed-context"
    if reason is None and ev.observed_at is not None and ev.fresh_until is not None:
        if ev.observed_at > ev.fresh_until or now > ev.fresh_until:
            reason = "stale-context"
    if reason is None and ev.sequence is not None and ev.source_head_sequence is not None:
        try:
            if tuple(ev.sequence) < tuple(ev.source_head_sequence):
                reason = "selected-sequence-before-source-head"
        except TypeError:
            reason = "cross-source-sequence"
    if reason is not None:
        public = ContextProjection(None, "unknown", ev.source or "unknown")
        return public, ContextEvidence(**{**ev.__dict__, "used_pct": None, "invalid_reason": reason})
    value = int(round(pct))
    public = ContextProjection(value, policy_band(value), ev.source or "unknown")
    return public, ev


def _route_record(entity, route_records=None):
    """Load one record, retaining a diagnostic reason without weakening old route.load()."""
    from . import route

    rid = _field(entity, "route_id")
    if not rid:
        return None, None
    records = route_records or {}
    if isinstance(records, dict) and rid in records:
        record = records[rid]
        if (record.get("route_id") != rid
                or (_field(entity, "route_hash") and record.get("route_hash") != _field(entity, "route_hash"))):
            return None, ROUTE_RECORD_MISMATCH
        return record, None
    path = _field(entity, "route_file")
    if not path:
        return None, ROUTE_RECORD_MISMATCH
    diagnostic = getattr(route, "load_diagnostic", None)
    if diagnostic:
        result = diagnostic(path, expect_hash=_field(entity, "route_hash"), expect_id=rid)
        return result.record, (None if result.valid else ROUTE_RECORD_MISMATCH)
    record = route.load(path, expect_hash=_field(entity, "route_hash"), expect_id=rid)
    return record, (None if record is not None else ROUTE_RECORD_MISMATCH)


def _active_node(node, state, job=None):
    progress = None
    raw_progress = node.get("progress")
    if isinstance(raw_progress, dict):
        progress = {"done": raw_progress.get("done", 0), "total": raw_progress.get("total", 0)}
    return ActiveNodeProjection(
        id=node.get("id"), depends_on=tuple(node.get("depends_on") or ()), level=node.get("level"),
        unit=node.get("unit"), unit_choices=tuple(node.get("unit_choices") or ()),
        gate=node.get("completion_gate", node.get("gate")),
        write_scope=node.get("write_scope"), state=state, progress=progress,
    )


def _record_view(record, route_id, jobs, node_evidence=None, now=None):
    """Use route.py's pure state resolver so projection and legacy route views agree."""
    from . import route
    return route._record_view(record, route_id, list(jobs), node_evidence or {},
                              time.time() if now is None else now)


def _record_nodes(record, route_id, jobs, node_evidence=None, now=None):
    if not isinstance(record, dict):
        return (), None
    view = _record_view(record, route_id, jobs, node_evidence=node_evidence, now=now)
    all_nodes = []
    for node in view.get("nodes", []):
        all_nodes.append(dict(node))
    projections = []
    for node in all_nodes:
        projections.append(ActiveNodeProjection(
            id=node.get("id"), depends_on=tuple(node.get("depends_on") or ()),
            level=node.get("level"), unit=node.get("unit"),
            unit_choices=tuple(node.get("unit_choices") or ()), gate=node.get("gate"),
            write_scope=node.get("write_scope"), state=node.get("state"),
            progress=node.get("progress"),
        ))
    return tuple(projections), view.get("progress")


def _active_stage_label(active_nodes):
    """Describe every active node in the sealed record order.

    Leaf projections may use their validated assigned contract, but an owner row
    represents the whole active route level.  Keeping this derivation here makes
    the owner projection independent of collector/job iteration order.
    """
    ids = [node.id for node in active_nodes if node.id]
    if not ids:
        return None
    if len(ids) == 1:
        return ids[0]
    return "{%s}" % ",".join(ids)


def _load_evidence_records(node_evidence, route_records):
    """Load records named only by terminal jobs.log evidence, without inventing routes."""
    from . import route
    records = dict(route_records or {})
    for rid, nodes in (node_evidence or {}).items():
        if rid in records:
            continue
        for evidence in (nodes or {}).values():
            path = _field(evidence, "route_file")
            if not path:
                continue
            record = route.load(path, expect_hash=_field(evidence, "route_hash"), expect_id=rid)
            if record is not None:
                records[rid] = record
                break
    return records


def _evidence_owner_candidates(entity, node_evidence, route_records):
    """Return route IDs whose terminal node evidence names this owner/conductor."""
    owner_ids = {_field(entity, "session_id"), _field(entity, "slug")}
    owner_ids.discard(None)
    candidates = []
    for rid, nodes in (node_evidence or {}).items():
        if any(_field(ev, "parent") in owner_ids for ev in (nodes or {}).values()):
            record = route_records.get(rid)
            if record is not None:
                candidates.append((rid, record, nodes or {}))
    return candidates


def _projection_from_record(entity, record, route_id, jobs, node_evidence=None, now=None,
                            route_node=None, owner=False):
    from . import route
    view = _record_view(record, route_id, jobs, node_evidence=node_evidence, now=now)
    nodes = tuple(view.get("nodes") or ())
    projections = tuple(ActiveNodeProjection(
        id=node.get("id"), depends_on=tuple(node.get("depends_on") or ()),
        level=node.get("level"), unit=node.get("unit"),
        unit_choices=tuple(node.get("unit_choices") or ()), gate=node.get("gate"),
        write_scope=node.get("write_scope"), state=node.get("state"), progress=None,
    ) for node in nodes)
    selected = next((node for node in projections if node.id == route_node), None)
    contract = _field(entity, "assigned_contract")
    active_nodes = tuple(node for node in projections if node.state == "active")
    if owner:
        label = _active_stage_label(active_nodes)
    elif contract and selected is not None:
        label = contract
    elif selected is not None:
        label = route_node
    elif len(active_nodes) == 1:
        label = active_nodes[0].id
    elif active_nodes:
        label = "{%s}" % ",".join(node.id for node in active_nodes)
    else:
        label = None
    return WorkProjection(
        source="route-exact", route_id=record.get("route_id", route_id),
        route_hash=record.get("route_hash"), route_node=route_node,
        attempt_id=_field(entity, "attempt_id"), assigned_contract=contract,
        unit=selected.unit if selected else _field(entity, "unit"), stage_label=label,
        node_state=selected.state if selected else None, active_nodes=active_nodes,
        progress=ProgressProjection(**(view.get("progress") or {"done": 0, "total": len(nodes)})),
        _route_view={"record": record, "nodes": nodes, "view": view},
    )


def _artifact_candidates(entity, artifact_root=None):
    slug = _field(entity, "slug") or _field(entity, "key")
    if not slug:
        return []
    roots = []
    for value in (artifact_root, _field(entity, "artifact_root"), _field(entity, "cwd")):
        if value:
            value = os.path.realpath(os.path.expanduser(str(value)))
            roots.extend((value, os.path.join(value, ".agent_reports")))
    candidates = set()
    for root in roots:
        for pattern in (os.path.join(root, "plans", "*_%s" % slug),
                        os.path.join(root, "*_%s" % slug)):
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    candidates.add(os.path.realpath(path))
    return sorted(candidates)


def exact_artifact_candidates(entity, artifact_root=None):
    """Expose exact-cardinality stage candidates for QA and hermetic tests."""
    return _artifact_candidates(entity, artifact_root=artifact_root)


def _artifact_stage(path):
    names = {os.path.basename(item) for item in glob.glob(os.path.join(path, "*"))}
    for label, markers in (("report", ("report", "verification")),
                           ("test", ("test",)), ("exec", ("execute",)),
                           ("plan", ("plan",))):
        if any(any(marker in name.lower() for marker in markers) for name in names):
            return label
    return None


def _explicit(entity):
    # An attempt identifies one launch, but it is not a route tuple.  Owners
    # carrying only attempt_id must still discover their children through the
    # explicit parent links below.
    return any(_field(entity, name) not in (None, "")
               for name in ("route_file", "route_id", "route_hash", "route_node"))


def _owner_children(entity, jobs):
    """Return only children named by the stable owner-link contracts."""
    sid = _field(entity, "session_id")
    slug = _field(entity, "slug")
    children = []
    for child in jobs:
        if sid and _field(child, "parent_sid") == sid:
            children.append(child)
        elif slug and _field(child, "parent_slug") == slug:
            children.append(child)
    return children


def _candidate_projection(entity, candidate, jobs, route_records, node_evidence, now):
    """Adopt one registered leaf candidate without reopening it at render time."""
    rid = _field(candidate, "route_id")
    record, failure = _route_record(candidate, route_records=route_records)
    route_node = _field(candidate, "route_node")
    if record is None or not route_node:
        return WorkProjection(
            source="registry-exact", route_id=rid,
            route_hash=_field(candidate, "route_hash"), route_node=route_node,
            attempt_id=_field(entity, "attempt_id"), node_state="unknown",
            ambiguity=failure or ROUTE_RECORD_MISMATCH,
        )
    same_jobs = [j for j in jobs if _field(j, "route_id") == rid]
    return _projection_from_record(
        entity, record, rid, same_jobs,
        node_evidence=(node_evidence or {}).get(rid, {}),
        now=now, route_node=route_node,
    )


def resolve_work_projection(entity, jobs=(), route_records=None, node_evidence=None,
                            artifact_root=None, now=None, _seen=None):
    """Resolve one entity using the approved evidence precedence."""
    seen = set() if _seen is None else _seen
    ident = (id(entity), _field(entity, "slug"), _field(entity, "session_id"))
    if ident in seen:
        return WorkProjection(ambiguity=OWNER_ROUTE_CONFLICT)
    seen.add(ident)
    pid, proc_start = _field(entity, "pid"), _field(entity, "proc_start")
    identity_evidence_present = pid is not None and proc_start is not None
    if identity_evidence_present:
        leaf_candidates = [j for j in jobs
                           if _field(j, "pid") == pid
                           and _field(j, "proc_start") == proc_start
                           and _field(j, "route_id")]
        if len(leaf_candidates) > 1:
            return WorkProjection(source="none", node_state="unknown",
                                  ambiguity=MULTIPLE_LEAF_CANDIDATES)
        if len(leaf_candidates) == 1 and not _explicit(entity):
            return _candidate_projection(entity, leaf_candidates[0], jobs, route_records,
                                         node_evidence, now)
    elif not _explicit(entity):
        cwd = _realpath(_field(entity, "cwd"))
        harness = _field(entity, "harness")
        cwd_candidates = [j for j in jobs
                          if _field(j, "route_id") and harness
                          and _field(j, "harness") == harness
                          and cwd and _realpath(_field(j, "cwd")) == cwd]
        if len(cwd_candidates) > 1:
            return WorkProjection(source="none", node_state="unknown",
                                  ambiguity=MULTIPLE_CHILD_CWD_CANDIDATES)
        if len(cwd_candidates) == 1:
            return _candidate_projection(entity, cwd_candidates[0], jobs, route_records,
                                         node_evidence, now)

    record, failure = _route_record(entity, route_records=route_records)
    explicit = _explicit(entity)
    if record is not None:
        expected_node = _field(entity, "route_node")
        nodes = record.get("nodes") or []
        node_ids = {n.get("id") for n in nodes if isinstance(n, dict)}
        if not expected_node or expected_node not in node_ids:
            failure = ROUTE_RECORD_MISMATCH
            record = None
        else:
            same_jobs = [j for j in jobs if _field(j, "route_id") == _field(entity, "route_id")]
            own = _projection_from_record(
                entity, record, _field(entity, "route_id"), same_jobs,
                node_evidence=(node_evidence or {}).get(_field(entity, "route_id"), {}),
                now=now, route_node=expected_node,
                owner=bool(_owner_children(entity, jobs)))
            # A direct owner route is valid only when every linked child agrees
            # with it.  Never silently privilege the owner's tuple over a child.
            child_projections = [resolve_work_projection(
                child, jobs=jobs, route_records=route_records,
                node_evidence=node_evidence, artifact_root=artifact_root,
                now=now, _seen=seen)
                for child in _owner_children(entity, jobs)]
            child_keys = {(p.route_id, p.route_hash) for p in child_projections
                          if p.source == "route-exact" and p.route_id}
            own_key = (own.route_id, own.route_hash)
            if any(key != own_key for key in child_keys):
                return WorkProjection(source="none", node_state="unknown",
                                      ambiguity=OWNER_ROUTE_CONFLICT)
            return own
    if explicit:
        return WorkProjection(
            source="registry-exact", route_id=_field(entity, "route_id"),
            route_hash=_field(entity, "route_hash"), route_node=_field(entity, "route_node"),
            attempt_id=_field(entity, "attempt_id"), assigned_contract=_field(entity, "assigned_contract"),
            unit=_field(entity, "unit"), stage_label=_field(entity, "assigned_contract") or _field(entity, "route_node"),
            node_state="unknown",
            ambiguity=failure or ROUTE_RECORD_MISMATCH,
        )

    # Owner route attribution is explicit parent-link traversal only.
    children = _owner_children(entity, jobs)
    child_projections = [resolve_work_projection(child, jobs=jobs, route_records=route_records,
                                                  node_evidence=node_evidence,
                                                  artifact_root=artifact_root, now=now, _seen=seen)
                         for child in children]
    for rid, record, evidence in _evidence_owner_candidates(entity, node_evidence, route_records or {}):
        child_projections.append(_projection_from_record(
            entity, record, rid, [j for j in jobs if _field(j, "route_id") == rid],
            node_evidence=evidence, now=now, owner=True))
    exact = [p for p in child_projections if p.source == "route-exact"]
    route_keys = {(p.route_id, p.route_hash) for p in exact}
    if len(route_keys) > 1:
        return WorkProjection(source="none", ambiguity=MULTIPLE_OWNER_ROUTES)
    if len(route_keys) == 1 and exact:
        p = exact[0]
        active = p.active_nodes
        return WorkProjection(source="route-exact", route_id=p.route_id, route_hash=p.route_hash,
                              active_nodes=active, progress=p.progress,
                              stage_label=_active_stage_label(active),
                              _route_view=p._route_view)

    # Artifact inference is the final fallback and is legal only when no route
    # tuple exists anywhere on this entity.  Owner candidates above therefore
    # always win, even when a plausible plan directory is present.
    candidates = _artifact_candidates(entity, artifact_root=artifact_root)
    if len(candidates) == 1:
        return WorkProjection(source="artifact-inferred", stage_label=_artifact_stage(candidates[0]))
    if len(candidates) > 1:
        return WorkProjection(source="none", ambiguity=MULTIPLE_ARTIFACT_PLAN_DIRS)
    # Without a route tuple or exact artifact evidence there is no observed
    # stage to project.  The renderer may show its honest pre-boot track, but
    # must not echo a manually supplied legacy stage token as current truth.
    return WorkProjection(source="none")


def resolve_projection(*args, **kwargs):
    """Compatibility alias for callers using the shorter v16 name."""
    return resolve_work_projection(*args, **kwargs)


def attach_projections(sessions: Iterable[Session], jobs: Iterable[DispatchJob],
                      route_records=None, node_evidence=None, artifact_root=None, now=None):
    """Attach exactly one work/context projection to every row and return both lists."""
    sessions, jobs = list(sessions), list(jobs)
    route_records = _load_evidence_records(node_evidence, route_records)
    all_entities = sessions + jobs
    for entity in all_entities:
        public, private = normalize_context(_evidence(entity), now=now)
        entity.context = public
        entity._context_evidence = private
    for entity in all_entities:
        entity.work_projection = resolve_work_projection(
            entity, jobs=jobs, route_records=route_records,
            node_evidence=node_evidence, artifact_root=artifact_root, now=now)
        entity.stage = entity.work_projection.stage_label if isinstance(entity, DispatchJob) else getattr(entity, "stage", None)
    return sessions, jobs


attach_work_projections = attach_projections


def route_summary_from_projections(entities):
    """Serialize route backing data already attached to rows; never reopens a route file."""
    out, seen = [], set()
    for entity in entities:
        projection = _field(entity, "work_projection")
        if not isinstance(projection, WorkProjection) or not projection.route_id:
            continue
        if projection.route_id in seen:
            continue
        seen.add(projection.route_id)
        backing = projection._route_view or {}
        record = backing.get("record") or {}
        legacy_view = backing.get("view") or {}
        nodes = []
        for node in legacy_view.get("nodes") or backing.get("nodes") or ():
            nodes.append(node.to_dict() if isinstance(node, ActiveNodeProjection) else dict(node))
        for node in nodes:
            # ``route._record_view`` keeps runtime job references for rendering;
            # public JSON is the additive route contract and must remain plain data.
            node.pop("job", None)
            node.pop("pid", None)
        ambiguity = projection.ambiguity
        if ambiguity is not None and not isinstance(ambiguity, list):
            ambiguity = [ambiguity]
        out.append({
            "route_id": projection.route_id,
            "route_hash": projection.route_hash or record.get("route_hash"),
            # Preserve the legacy route.summary values from the attached
            # backing view; v16 fields remain additive.
            "source": legacy_view.get("source", "record"),
            "capability": legacy_view.get("capability", record.get("capability")),
            "capability_mode": legacy_view.get("capability_mode", record.get("capability_mode")),
            "execution_topology": legacy_view.get("execution_topology", record.get("execution_topology")),
            "unit_catalog_digest": legacy_view.get("unit_catalog_digest", record.get("unit_catalog_digest")),
            "composed": bool(legacy_view.get("composed", record.get("composed"))),
            "effective_intensity": legacy_view.get("effective_intensity", record.get("effective_intensity")),
            "progress": legacy_view.get("progress", projection.progress.to_dict() if projection.progress else None),
            "ambiguity": ambiguity,
            "nodes": nodes,
        })
    return out
