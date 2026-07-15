"""Claude Code enrichment — passive, read-only (01_tap_mechanics.md §1).

Two on-disk sources per session:
  1. ~/.claude/sessions/<pid>.json  — native claude file: sessionId, status(idle/shell/busy),
     name, cwd. No model/tokens/rate-limit here.
  2. ~/.claude/.statusline/<sid>.json — per-session statusline tap (§5, written by
     statusline.sh). Full telemetry: model, effort, context%, 5h/7d rate limits, cost.
     Absent until §5 has run for that session → those cells stay '—' (graceful).

Liveness signal = newest transcript mtime (projects/<enc-cwd>/*.jsonl), falling back to
sessions/<pid>.json statusUpdatedAt.
"""
import datetime
import json
import os
import re

from ..model import SubAgent


def _home():
    """Runtime config home (projects/sessions/.statusline) — Claude Code config dir."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def _enc_cwd(cwd):
    # projects dir encoding: '/', '.', '_' → '-' (matches dispatch-liveness.sh sed).
    return "".join("-" if ch in "/._" else ch for ch in cwd)


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _newest_transcript_path(home, cwd, sid):
    """Transcript path for liveness/title extraction: `<sid>.jsonl` when the session id
    is known, else the newest .jsonl in the project dir. Shared by mtime and ai-title
    lookups so both use the same resolved path (one os.listdir scan, not two).

    A known sid whose transcript is MISSING returns None instead of falling back:
    borrowing the newest neighbor .jsonl stamps another same-cwd session's fresh
    mtime/title onto this row (observed 2026-07-15: a 33h-old orphaned Orca-relay
    session rendered as just-active with a stolen title). mtime then degrades to
    the session file's statusUpdatedAt in enrich()."""
    if not cwd:
        return None
    proj = os.path.join(home, "projects", _enc_cwd(cwd))
    if sid:
        p = os.path.join(proj, sid + ".jsonl")
        return p if _mtime(p) is not None else None
    best, best_m = None, None
    try:
        for name in os.listdir(proj):
            if name.endswith(".jsonl"):
                p = os.path.join(proj, name)
                m = _mtime(p)
                if m is not None and (best_m is None or m > best_m):
                    best, best_m = p, m
    except OSError:
        pass
    return best


def _newest_transcript_mtime(home, cwd, sid):
    path = _newest_transcript_path(home, cwd, sid)
    return _mtime(path) if path else None


_TITLE_JUNK_RE = re.compile(r"^(new session\b|\d{4}-\d{2}-\d{2}[t ]\d{2}:\d{2})", re.IGNORECASE)


_TITLE_CACHE = {}   # path -> (mtime, size, title) — avoid rescanning an unchanged transcript every tick


def _tail_ai_title(path, chunk=8192, max_scan=None):
    """Last `ai-title` line's aiTitle value, scanning backward from EOF in growing
    windows (chunk, ×8 each step) until an ai-title line is seen or the whole file
    is covered. Long sessions keep appending messages after the title lines, so a
    fixed tail window misses them (observed titles can sit 31–100KB before EOF) —
    the growing scan keeps short-session cost at one small read while still
    reaching early titles. A transcript can carry several ai-title lines appended
    over the session's life (renamed/refined) — the last one wins. tolerant:
    malformed json lines are skipped, a missing/empty/placeholder ("New session …",
    bare ISO timestamp) title → None so the caller falls back to slug. Results are
    memoized per (mtime, size) so unchanged files are not re-read on every tick."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    cached = _TITLE_CACHE.get(path)
    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
        return cached[2]
    sz = st.st_size
    limit = sz if max_scan is None else min(sz, max_scan)
    window = chunk
    title = None
    found_line = False
    while True:
        start = max(0, sz - window)
        try:
            with open(path, "rb") as f:
                f.seek(start)
                data = f.read().decode("utf-8", "replace")
        except OSError:
            return None
        lines = data.splitlines()
        if start > 0 and lines:
            lines = lines[1:]                       # drop the partial first line
        for ln in lines:
            if '"ai-title"' not in ln:
                continue
            try:
                d = json.loads(ln)
            except Exception:
                continue
            if "aiTitle" not in d:
                continue
            found_line = True
            t = d.get("aiTitle")
            title = t.strip() if isinstance(t, str) and t.strip() else None
        if found_line or window >= limit:
            break
        window = min(window * 8, limit)
    if title and _TITLE_JUNK_RE.match(title):
        title = None
    _TITLE_CACHE[path] = (st.st_mtime, st.st_size, title)
    return title


_SUBAGENT_CACHE = {}   # path -> (mtime, size, [SubAgent,...]) — separate from _TITLE_CACHE;
                        # same (mtime, size) key pattern, independent invalidation.


def _ts_to_epoch(ts):
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _tail_subagents(path, chunk=8192, max_scan=None):
    """Sub-agent rows from Task tool_use/tool_result pairing (prd.md:292 Claude source,
    `isSidechain: true` marks the spawned sub-agent's own turns; the pairing itself lives
    on the Task tool_use/tool_result pair in the PARENT thread). Grows backward exactly
    like `_tail_ai_title` — same window, same guarantee (R3-1): if a tool_use is inside the
    scanned window, any tool_result answering it is necessarily ALSO inside it (an
    append-only log only grows forward), so "unpaired tool_use" found here is structurally
    ACTIVE, never a scan-window artifact. The converse (a tool_result whose tool_use fell
    outside the window) is silently dropped — that pairing describes a COMPLETED sub-agent,
    which is hidden by default anyway (prd.md:293), so missing it costs nothing.

    Tolerant by contract (F-3): any malformed line is skipped. Returns None only when the
    file itself cannot be read (honest "no source", prd.md:292 — never a guess).
    """
    try:
        st = os.stat(path)
    except OSError:
        return None
    cached = _SUBAGENT_CACHE.get(path)
    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
        return cached[2]
    sz = st.st_size
    limit = sz if max_scan is None else min(sz, max_scan)
    window = chunk
    calls = {}      # tool_use_id -> SubAgent
    resolved = set()
    while True:
        start = max(0, sz - window)
        try:
            with open(path, "rb") as f:
                f.seek(start)
                data = f.read().decode("utf-8", "replace")
        except OSError:
            return None
        lines = data.splitlines()
        if start > 0 and lines:
            lines = lines[1:]           # drop the partial first line
        for ln in lines:
            if "tool_use" not in ln and "tool_result" not in ln:
                continue
            try:
                d = json.loads(ln)
            except Exception:
                continue
            msg = d.get("message") if isinstance(d, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use" and c.get("name") == "Task":
                    tid = c.get("id")
                    if not tid or tid in calls:
                        continue
                    inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                    calls[tid] = SubAgent(agent_type=inp.get("subagent_type"), active=True,
                                          started_at=_ts_to_epoch(d.get("timestamp")),
                                          source="claude-sidechain")
                elif c.get("type") == "tool_result":
                    tid = c.get("tool_use_id")
                    if tid:
                        resolved.add(tid)
        if window >= limit:
            break
        window = min(window * 8, limit)
    out = []
    for tid, sa in calls.items():
        if tid in resolved:
            sa.active = False
        out.append(sa)
    out.sort(key=lambda sa: sa.started_at or 0, reverse=True)
    _SUBAGENT_CACHE[path] = (st.st_mtime, st.st_size, out)
    return out


def _apply_statusline(sess, d):
    m = d.get("model") or {}
    sess.model = m.get("display_name") or m.get("id") or sess.model
    eff = (d.get("effort") or {}).get("level")
    if eff:
        sess.effort = eff
    cw = d.get("context_window") or {}
    up = cw.get("used_percentage")
    if isinstance(up, (int, float)):
        sess.ctx_pct = min(99, round(up))
    current = cw.get("current_usage") or {}
    if isinstance(current, dict):
        active_parts = [
            current.get("input_tokens"),
            current.get("cache_creation_input_tokens"),
            current.get("cache_read_input_tokens"),
        ]
        if any(isinstance(value, (int, float)) for value in active_parts):
            sess.active_context_tokens = int(sum(
                value for value in active_parts if isinstance(value, (int, float))))
    window = cw.get("context_window_size")
    if isinstance(window, (int, float)) and window > 0:
        sess.context_window_tokens = int(window)
    ti, to = cw.get("total_input_tokens"), cw.get("total_output_tokens")
    if isinstance(ti, (int, float)) or isinstance(to, (int, float)):
        sess.tokens = int((ti or 0) + (to or 0))
        sess.session_input_tokens = int(ti) if isinstance(ti, (int, float)) else None
        sess.session_output_tokens = int(to) if isinstance(to, (int, float)) else None
        sess.session_total_tokens = sess.tokens
    rl = d.get("rate_limits") or {}

    def pct(k):
        v = (rl.get(k) or {}).get("used_percentage")
        return round(v) if isinstance(v, (int, float)) else None

    p5, p7 = pct("five_hour"), pct("seven_day")
    if p5 is not None:
        sess.rl_5h = p5
    if p7 is not None:
        sess.rl_7d = p7
    # per-model buckets → rl_ms [["fable", 57], ...]. Two schema shapes (2.1.198 bundle):
    #  1. named siblings: seven_day_opus / seven_day_sonnet / seven_day_overage_included
    #     ("Fable 5 limit" label) / seven_day_oauth_apps — same {used_percentage} shape as 5h/7d
    #  2. model_scoped array: [{display_name:"Fable", utilization:0..1, resets_at:str}]
    ms = []
    for k, lbl in (("seven_day_opus", "opus"), ("seven_day_sonnet", "sonnet"),
                   ("seven_day_overage_included", "fable"), ("seven_day_oauth_apps", "apps")):
        v = pct(k)
        if v is not None:
            ms.append([lbl, v])
    for e in (rl.get("model_scoped") or []):
        if isinstance(e, dict) and isinstance(e.get("utilization"), (int, float)):
            lbl = (e.get("display_name") or "model").split()[0].lower()
            if not any(x[0] == lbl for x in ms):     # named bucket wins over a duplicate scoped row
                ms.append([lbl, round(e["utilization"] * 100)])
    if ms:
        sess.rl_ms = ms
    cost = d.get("cost") or {}
    cv = cost.get("total_cost_usd") if isinstance(cost, dict) else None
    if isinstance(cv, (int, float)):
        sess.cost = cv


def read_registry(pid, home=None):
    """~/.claude/sessions/<pid>.json → dict, or None.

    F-26 promotes this file from an incidental status lookup to a first-class tier-1
    source: it is the runtime declaring its own identity, name, and activity window.
    Tolerant by contract — a session file written milliseconds ago may not carry
    `status`/`updatedAt` yet, and a missing/corrupt file is simply silence (None).
    """
    try:
        with open(os.path.join(home or _home(), "sessions", "%d.json" % int(pid))) as f:
            d = json.load(f)
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def _ms_to_sec(v):
    """registry epoch-ms → epoch-sec; anything non-numeric (or bool) → None."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v / 1000.0


def _apply_registry(sess, sj):
    """Load every tier-1 registry field onto the Session. Each key is independently
    optional: a fresh row carrying only pid/sessionId must not lose the ones it has."""
    sess.session_id = sj.get("sessionId") or sess.session_id
    sess.status = sj.get("status")                # idle | shell | busy | (absent → None)
    name = sj.get("name")
    if name:
        sess.slug = name                          # friendly name disambiguates same-cwd sessions
        sess.registry_name = name                 # explicit link in the name chain (F-26)
    kind = sj.get("kind")
    if isinstance(kind, str):
        sess.kind = kind
    ps = sj.get("procStart")
    if ps is not None and not isinstance(ps, bool):
        sess.registry_proc_start = str(ps)        # compared against /proc in the classifier
    sess.started_at = _ms_to_sec(sj.get("startedAt"))
    sess.updated_at = _ms_to_sec(sj.get("updatedAt"))


def enrich(sess):
    home = _home()

    # 1) native per-pid registry file — tier-1 source (F-26)
    sj = read_registry(sess.pid, home)
    if sj is not None:
        _apply_registry(sess, sj)

    # 2) per-session statusline tap (§5) — telemetry; absent → '—'
    sid = sess.session_id
    if sid:
        try:
            with open(os.path.join(home, ".statusline", sid + ".json")) as f:
                tj = json.load(f)
            if isinstance(tj, dict):
                _apply_statusline(sess, tj)
        except Exception:
            pass

    # 3) Liveness mtime and title. Priority: fresh sidecar, AI title, then slug.
    path = _newest_transcript_path(home, sess.cwd, sid)
    if path:
        sess._transcript_path = path              # ephemeral: live title scheduler, not --json
    # Transcript presence is the §2.2 `unused` refinement input: a session that has NEVER
    # been prompted has no transcript at all. Ephemeral (leading underscore) — evidence for
    # the classifier, not a --json field.
    sess._has_transcript = bool(path)
    if path:
        subs = _tail_subagents(path)
        if subs is not None:
            sess.subagents = subs
    m = _mtime(path) if path else None
    if m is None and isinstance(sj, dict):
        su = sj.get("statusUpdatedAt") or sj.get("updatedAt")
        if isinstance(su, (int, float)):
            m = su / 1000.0                        # ms → s
            # This mtime is the registry's own clock, not real activity — a tier-3 stand-in.
            sess._mtime_from_registry = True
    sess.mtime = m
    # 3a) A fresh neutral sidecar overrides the AI title; failures pass through safely.
    from fleet import titles                      # Deferred import; no cycle, standard library only.
    st = titles.fresh_title(sid, harness="claude") if sid else None
    if st:
        sess.title = st
    elif path:                                     # 3b) F-14 ai-title fallback
        t = _tail_ai_title(path)
        if t:
            sess.title = t
    # Otherwise render falls back from a missing title to the registry name, then the slug.

    # 4) provenance (F-26) — resolved LAST, and only for a session that has no title. A titled
    # session already says what it is; "who launched this?" is only an open question for a row
    # with no self-description (the never-prompted ghost being the motivating case). Gating on
    # title also keeps the tag off every ordinary row, where it would just eat the name zone.
    # Best-effort by contract: any failure leaves None and renders no tag (PRD F-26 —
    # misattribution is worse than absence).
    if sess.provenance is None and not sess.title:
        from . import procscan
        try:
            sess.provenance = procscan.provenance(sess.pid)
        except Exception:
            sess.provenance = None
