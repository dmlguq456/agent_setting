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
import json
import os
import re


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
    """Transcript path for liveness/title extraction: prefer `<sid>.jsonl`, else the
    newest .jsonl in the project dir. Shared by mtime and ai-title lookups so both use
    the same resolved path (one os.listdir scan, not two)."""
    if not cwd:
        return None
    proj = os.path.join(home, "projects", _enc_cwd(cwd))
    if sid:
        p = os.path.join(proj, sid + ".jsonl")
        if _mtime(p) is not None:
            return p
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


def _tail_ai_title(path, chunk=8192):
    """Last `ai-title` line's aiTitle value within the file's trailing `chunk` bytes.
    A transcript can carry several ai-title lines appended over the session's life
    (renamed/refined) — the last one wins. tolerant: malformed json lines are skipped,
    a missing/empty/placeholder ("New session …", bare ISO timestamp) title → None so
    the caller falls back to slug."""
    try:
        sz = os.path.getsize(path)
        start = max(0, sz - chunk)
        with open(path, "rb") as f:
            f.seek(start)
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    lines = data.splitlines()
    if start > 0 and lines:
        lines = lines[1:]                           # drop the partial first line
    title = None
    for ln in lines:
        if '"ai-title"' not in ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        t = d.get("aiTitle")
        if isinstance(t, str) and t.strip():
            title = t.strip()
    if title and _TITLE_JUNK_RE.match(title):
        return None
    return title


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
    ti, to = cw.get("total_input_tokens"), cw.get("total_output_tokens")
    if isinstance(ti, (int, float)) or isinstance(to, (int, float)):
        sess.tokens = int((ti or 0) + (to or 0))
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


def enrich(sess):
    home = _home()

    # 1) native per-pid status file
    sj = None
    try:
        with open(os.path.join(home, "sessions", "%d.json" % sess.pid)) as f:
            sj = json.load(f)
    except Exception:
        sj = None
    if isinstance(sj, dict):
        sess.session_id = sj.get("sessionId") or sess.session_id
        sess.status = sj.get("status")            # idle | shell | busy
        name = sj.get("name")
        if name:                                   # friendly name disambiguates same-cwd sessions
            sess.slug = name

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

    # 3) liveness mtime + ai-title (F-14) — resolve the transcript path once, use it for both
    path = _newest_transcript_path(home, sess.cwd, sid)
    m = _mtime(path) if path else None
    if m is None and isinstance(sj, dict):
        su = sj.get("statusUpdatedAt") or sj.get("updatedAt")
        if isinstance(su, (int, float)):
            m = su / 1000.0                        # ms → s
    sess.mtime = m
    if path:
        t = _tail_ai_title(path)
        if t:
            sess.title = t
