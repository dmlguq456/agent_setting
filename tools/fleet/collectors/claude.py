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


def _home():
    return (os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
            or os.path.expanduser("~/.claude"))


def _enc_cwd(cwd):
    # projects dir encoding: '/', '.', '_' → '-' (matches dispatch-liveness.sh sed).
    return "".join("-" if ch in "/._" else ch for ch in cwd)


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _newest_transcript_mtime(home, cwd, sid):
    if not cwd:
        return None
    proj = os.path.join(home, "projects", _enc_cwd(cwd))
    if sid:
        m = _mtime(os.path.join(proj, sid + ".jsonl"))
        if m is not None:
            return m
    best = None
    try:
        for name in os.listdir(proj):
            if name.endswith(".jsonl"):
                m = _mtime(os.path.join(proj, name))
                if m is not None and (best is None or m > best):
                    best = m
    except OSError:
        pass
    return best


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

    # 3) liveness mtime
    m = _newest_transcript_mtime(home, sess.cwd, sid)
    if m is None and isinstance(sj, dict):
        su = sj.get("statusUpdatedAt") or sj.get("updatedAt")
        if isinstance(su, (int, float)):
            m = su / 1000.0                        # ms → s
    sess.mtime = m
