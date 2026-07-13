"""opencode enrichment — passive, read-only SQLite (01_tap_mechanics.md §3).

State lives in ~/.local/share/opencode/opencode.db (WAL; opened mode=ro). The `session` table
carries per-session model/cwd/cost/tokens live. argv has no session id, so pid↔session is
matched by /proc/cwd == session.directory; among sessions in that directory we take the most
recently updated top-level (parent_id IS NULL) session.

Structurally missing (render '—', PRD §2/§4): rate-limit (no column). effort = model.variant.
context% = last-request prompt size (input + cache.read + cache.write from the latest
assistant message's tokens object) / model context window, the window read from opencode's
own models.dev registry cache (~/.cache/opencode/models.json). The session-table column
tokens_input is a cumulative cost-side aggregate, NOT the current context size.
"""
import json
import os
import sqlite3
import time

_COLS = ("id, slug, agent, model, cost, tokens_input, tokens_output, tokens_reasoning, "
         "time_updated, parent_id")

_REG = {"ts": 0.0, "map": None}          # model-id/leaf → context window (from models.json)
_REG_TTL = 300.0


def _model_ctx_limit(model_id):
    """Context window for a model id, from opencode's models.dev registry cache
    (~/.cache/opencode/models.json — the same source opencode's own TUI uses for context%).
    None when unavailable → ctx% stays '—'. Cached 5 min."""
    if not model_id:
        return None
    now = time.time()
    if _REG["map"] is None or now - _REG["ts"] > _REG_TTL:
        m = {}
        path = os.environ.get("OPENCODE_MODELS") or os.path.expanduser("~/.cache/opencode/models.json")
        try:
            with open(path, encoding="utf-8") as f:
                reg = json.load(f)
            for prov in (reg.values() if isinstance(reg, dict) else []):
                models = prov.get("models") if isinstance(prov, dict) else None
                if not isinstance(models, dict):
                    continue
                for mkey, mdef in models.items():
                    lim = mdef.get("limit") if isinstance(mdef, dict) else None
                    ctx = lim.get("context") if isinstance(lim, dict) else None
                    if isinstance(ctx, (int, float)) and ctx > 0:
                        for k in (mkey, mkey.split("/")[-1]):      # match bare id or provider/org-prefixed
                            if m.get(k, 0) < ctx:
                                m[k] = int(ctx)
        except Exception:
            m = {}
        _REG.update(ts=now, map=m)
    reg = _REG["map"] or {}
    return reg.get(model_id) or reg.get(model_id.split("/")[-1])


def _db():
    return os.environ.get("OPENCODE_DB") or os.path.expanduser(
        "~/.local/share/opencode/opencode.db")


def _query(cur, cwd):
    # prefer a top-level session; fall back to any session in the directory
    for extra in ("AND parent_id IS NULL ", ""):
        row = cur.execute(
            "SELECT %s FROM session WHERE directory=? %s"
            "ORDER BY time_updated DESC LIMIT 1" % (_COLS, extra),
            (cwd,),
        ).fetchone()
        if row:
            return row
    return None


def _context_tokens_from_payload(payload):
    tokens = payload.get("tokens") if isinstance(payload, dict) else None
    if not isinstance(tokens, dict):
        return None
    cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
    total = 0
    for value in (tokens.get("input"), cache.get("read"), cache.get("write")):
        if isinstance(value, (int, float)):
            total += value
    return total or None


def _last_request_context(con, sid):
    """Latest assistant step prompt size, excluding output/cumulative session totals."""
    for table in ("message", "part", "session_message"):
        try:
            rows = con.execute(
                "SELECT data FROM %s WHERE session_id=? ORDER BY time_updated DESC LIMIT 50" % table,
                (sid,),
            )
        except Exception:
            continue
        for (data,) in rows:
            try:
                payload = json.loads(data) or {}
            except Exception:
                continue
            ctx = _context_tokens_from_payload(payload)
            if ctx:
                return ctx
    return None


def enrich(sess):
    db = _db()
    if not sess.cwd or not os.path.exists(db):
        return
    con = None
    last_ctx = None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=1.0)
        row = _query(con.cursor(), sess.cwd)
        if row and row[0]:
            last_ctx = _last_request_context(con, row[0])
            try:
                tr = con.execute(
                    "SELECT title FROM session WHERE id=? LIMIT 1", (row[0],)).fetchone()
                if tr and tr[0] and str(tr[0]).strip():
                    sess.title = str(tr[0]).strip()
            except Exception:
                pass   # older DB without a title column → title stays None (tolerant, F-3)
    except Exception:
        return
    finally:
        if con is not None:
            con.close()
    if not row:
        return
    sid, slug, agent, model_j, cost, ti, to, tr, tupd, _parent = row
    if sid:
        sess.session_id = sid
    if slug:
        sess.slug = slug
    if model_j:
        try:
            mj = json.loads(model_j) or {}
            sess.model = mj.get("id") or model_j
            # opencode reasoning effort = model JSON 'variant' (e.g. high/low) — user 2026-07-01
            if mj.get("variant"):
                sess.effort = mj.get("variant")
        except Exception:
            sess.model = model_j
    if isinstance(cost, (int, float)):
        sess.cost = cost
    toks = sum(x for x in (ti, to, tr) if isinstance(x, (int, float)))
    sess.tokens = toks or None
    sess.session_input_tokens = int(ti) if isinstance(ti, (int, float)) else None
    sess.session_output_tokens = int(to) if isinstance(to, (int, float)) else None
    sess.session_reasoning_output_tokens = int(tr) if isinstance(tr, (int, float)) else None
    sess.session_total_tokens = toks or None
    # context% = current-context size (last API request's prompt ~ what the model
    # actually saw as context) / model window (registry). NOT session.tokens_input,
    # which is cumulative API input across all requests in the session — cost-side,
    # not context-side. The real last-request context size lives in the data JSON of
    # the latest assistant message: tokens.input + tokens.cache.read +
    # tokens.cache.write. Falls back to session.tokens_input only when per-message
    # tokens are unavailable.
    ctx_for_pct = last_ctx if last_ctx else (ti if isinstance(ti, (int, float)) else None)
    if isinstance(ctx_for_pct, (int, float)) and ctx_for_pct:
        sess.active_context_tokens = int(ctx_for_pct)
        lim = _model_ctx_limit(sess.model)
        if lim:
            sess.context_window_tokens = int(lim)
            sess.ctx_pct = min(99, round(100 * ctx_for_pct / lim))
    if isinstance(tupd, (int, float)):
        sess.mtime = tupd / 1000.0                  # ms → s
    # rl_5h / rl_7d: opencode has no rate-limit column → left None ('—').
