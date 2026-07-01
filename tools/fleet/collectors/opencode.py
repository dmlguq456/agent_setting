"""opencode enrichment — passive, read-only SQLite (01_tap_mechanics.md §3).

State lives in ~/.local/share/opencode/opencode.db (WAL; opened mode=ro). The `session` table
carries per-session model/cwd/cost/tokens live. argv has no session id, so pid↔session is
matched by /proc/cwd == session.directory; among sessions in that directory we take the most
recently updated top-level (parent_id IS NULL) session.

Structurally missing (render '—', PRD §2/§4): rate-limit, effort, context% (no window column).
"""
import json
import os
import sqlite3

_COLS = ("id, slug, agent, model, cost, tokens_input, tokens_output, tokens_reasoning, "
         "time_updated, parent_id")


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


def enrich(sess):
    db = _db()
    if not sess.cwd or not os.path.exists(db):
        return
    con = None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=1.0)
        row = _query(con.cursor(), sess.cwd)
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
    if isinstance(tupd, (int, float)):
        sess.mtime = tupd / 1000.0                  # ms → s
    # rl_5h / rl_7d / ctx_pct: opencode has no rate-limit column and no context-window field
    # (only cumulative token counts) → left None ('—'). effort now sourced from model.variant above.
