"""Codex CLI enrichment — passive, read-only (01_tap_mechanics.md §2).

Codex writes no per-session status file; telemetry is recovered from the rollout jsonl:
  ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl
  · line 1  = session_meta  → payload.cwd (pid↔session match key)
  · last "token_count" event → payload.info.{last_token_usage, model_context_window}
      + payload.rate_limits.{primary,secondary}.used_percent
Model/effort default from ~/.codex/config.toml (top-level model / model_reasoning_effort).

context% = last_token_usage.input_tokens / model_context_window (each turn resends the full
context as input, so the last request's input ≈ current context occupancy — validated 2026-07-01;
cumulative total_token_usage is NOT context occupancy).

Empirical (25 live rollouts, 2026-07-01): last_token_usage.input_tokens ALREADY includes
cached_input_tokens (cached ≤ input in every case); (input+cached)/window yields impossible
121-178% — additive hypothesis REJECTED. Formula stays input_tokens/model_context_window with
min(99) clamp (see _apply_token_count). Do NOT change the formula.

A per-tick cache (cwd → newest rollout path) is built from cheap line-1 reads of all rollouts
(≈200 files); the expensive last-token-count parse touches only a 64 KB tail of the matched file.
"""
import json
import os
import re
import time

# rollout filename tail: rollout-<ISO-ts>-<uuid>.jsonl
_SID_RE = re.compile(r"-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$")

_INDEX = {"ts": 0.0, "map": None}          # cwd → newest rollout path
_INDEX_TTL = 1.5
_CFG = {"ts": 0.0, "model": None, "effort": None}


def _home():
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def _config_model_effort(home):
    now = time.time()
    if now - _CFG["ts"] < 10.0 and (_CFG["model"] or _CFG["effort"]):
        return _CFG["model"], _CFG["effort"]
    model = effort = None
    try:
        with open(os.path.join(home, "config.toml"), encoding="utf-8", errors="replace") as f:
            for ln in f:
                s = ln.strip()
                if s.startswith("["):              # stop at first [section] — top-level keys only
                    break
                if not s or s.startswith("#") or "=" not in s:
                    continue
                key, _, val = s.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key == "model":
                    model = val
                elif key == "model_reasoning_effort":
                    effort = val
    except Exception:
        pass
    _CFG.update(ts=now, model=model, effort=effort)
    return model, effort


def _rollout_cwd(path):
    """cwd from session_meta (line 1) — cheap single-line read."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            m = json.loads(f.readline())
        if m.get("type") == "session_meta":
            return (m.get("payload") or {}).get("cwd")
    except Exception:
        pass
    return None


def _index(home):
    now = time.time()
    if _INDEX["map"] is not None and now - _INDEX["ts"] < _INDEX_TTL:
        return _INDEX["map"]
    base = os.path.join(home, "sessions")
    files = []
    for root, _dirs, names in os.walk(base):
        for n in names:
            if n.startswith("rollout-") and n.endswith(".jsonl"):
                p = os.path.join(root, n)
                try:
                    files.append((os.path.getmtime(p), p))
                except OSError:
                    pass
    files.sort(reverse=True)                        # newest first → first per cwd wins
    m = {}
    for _mt, p in files:
        cwd = _rollout_cwd(p)
        if cwd and cwd not in m:
            m[cwd] = p
    _INDEX.update(ts=now, map=m)
    return m


def _tail_token_count(path, chunk=65536):
    """Last '"token_count"' line within the file's trailing `chunk` bytes."""
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
    last = None
    for ln in lines:
        if '"token_count"' in ln:
            last = ln
    return last


def _apply_token_count(sess, line):
    # Formula is input_tokens/model_context_window (min(99) clamp) — NOT (input+cached)/window.
    # See module docstring: 25-rollout empirical check (2026-07-01) rejected the additive
    # hypothesis (it produced impossible 121-178% values). input_tokens already includes cache.
    try:
        p = json.loads(line).get("payload") or {}
    except Exception:
        return
    info = p.get("info") or {}
    win = info.get("model_context_window")
    ltu = info.get("last_token_usage") or {}
    cur_in = ltu.get("input_tokens")                # includes cached — ≈ current context size
    if isinstance(cur_in, (int, float)):
        sess.tokens = int(cur_in)
        if isinstance(win, (int, float)) and win:
            sess.ctx_pct = min(99, round(100 * cur_in / win))
    rl = p.get("rate_limits") or {}

    def rp(k):
        v = (rl.get(k) or {}).get("used_percent")
        return round(v) if isinstance(v, (int, float)) else None

    p5, p7 = rp("primary"), rp("secondary")         # 300min ≈ 5h · 10080min = 7d
    if p5 is not None:
        sess.rl_5h = p5
    if p7 is not None:
        sess.rl_7d = p7


def enrich(sess):
    home = _home()
    model, effort = _config_model_effort(home)
    if model:
        sess.model = model
    if effort:
        sess.effort = effort
    if not sess.cwd:
        return
    path = _index(home).get(sess.cwd)
    if not path:
        return                                       # no matching rollout → telemetry stays '—'
    if sess.app_server:
        # app-server companion: sess.cwd here is the leaf's OWN cwd (/proc/<pid>/cwd),
        # NOT the project --cwd — the real --cwd lives on the sibling node broker process,
        # a different comm that procscan does not scan. So _index(home).get(sess.cwd) may
        # match a WRONG/OLD interactive rollout purely by cwd coincidence. Attaching that
        # rollout's mtime as a liveness signal would be dishonest (it belongs to an
        # unrelated session), so we set only what's honest: skip session_id + the token
        # block entirely, and explicitly null out mtime rather than inherit the mismatched
        # value. With mtime=None, liveness falls back to alive-process → idle.
        sess.mtime = None
        return
    sid = _SID_RE.search(os.path.basename(path))
    if sid:
        sess.session_id = sid.group(1)
    try:
        sess.mtime = os.path.getmtime(path)
    except OSError:
        sess.mtime = None
    tc = _tail_token_count(path)
    if tc:
        _apply_token_count(sess, tc)
