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
    p5, p7 = _rates_from_payload(p)                 # 300min ≈ 5h · 10080min = 7d
    if p5 is not None:
        sess.rl_5h = p5
    if p7 is not None:
        sess.rl_7d = p7


def _rates_from_payload(p):
    """(rl_5h, rl_7d) from a token_count payload, EXPIRY-AWARE: rollout samples freeze at the
    last activity, so a window whose resets_at has since passed shows its PRE-reset value (e.g.
    a 17h-old 3% — or 94% — for the 5h window). No newer sample ⇒ no local consumption since ⇒
    the current window is effectively 0%. (2026-07-02 user: codex usage looked wrong.)"""
    rl = p.get("rate_limits") or {}

    def rp(k):
        d = rl.get(k) or {}
        v = d.get("used_percent")
        if not isinstance(v, (int, float)):
            return None
        rs = d.get("resets_at")
        if isinstance(rs, (int, float)) and rs < time.time():
            return 0
        return round(v)

    return rp("primary"), rp("secondary")


_ACCT = {"ts": 0.0, "data": None}


def _api_usage():
    """LIVE account usage via the same endpoint the codex TUI itself uses (`/wham/usage`,
    bundle: account/usage/read) — read-only GET with the user's own OAuth token from auth.json.
    Rollout samples only update when a session is actually USED (user 2026-07-02: '세션을 켜서
    한번 써야 업데이트'), so an active probe is the reliable primary source. None on any failure
    (expired token, offline, schema change) — the rollout scan below remains the fallback."""
    try:
        with open(os.path.join(_home(), "auth.json")) as f:
            a = json.load(f)
        toks = a.get("tokens") or {}
        tok, acc = toks.get("access_token"), toks.get("account_id")
    except Exception:
        return None
    if not tok:
        return None
    import urllib.request
    req = urllib.request.Request(
        "https://chatgpt.com/backend-api/wham/usage",
        headers={"Authorization": "Bearer " + tok,
                 "chatgpt-account-id": acc or "",
                 "User-Agent": "codex-cli"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.load(r)
    except Exception:
        return None
    rl = (d if isinstance(d, dict) else {}).get("rate_limit") or {}

    def rp(k):
        v = (rl.get(k) or {}).get("used_percent")
        return round(v) if isinstance(v, (int, float)) else None

    p5, p7 = rp("primary_window"), rp("secondary_window")
    return (p5, p7) if (p5 is not None or p7 is not None) else None


def account_usage():
    """Account-level (rl_5h, rl_7d): live API first (see _api_usage), then the NEWEST on-disk
    rollout carrying rate_limits (expiry rule applied) as offline fallback. TTL-cached 60s."""
    now = time.time()
    if now - _ACCT["ts"] <= 60.0:
        return _ACCT["data"]
    _ACCT["ts"] = now
    _ACCT["data"] = _api_usage()
    if _ACCT["data"] is not None:
        return _ACCT["data"]
    files = []
    root = os.path.join(_home(), "sessions")
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            if n.endswith(".jsonl"):
                p = os.path.join(dirpath, n)
                try:
                    files.append((os.path.getmtime(p), p))
                except OSError:
                    pass
    for _mt, path in sorted(files, reverse=True)[:12]:   # newest first, first rate hit wins
        line = _tail_token_count(path)
        if not line:
            continue
        try:
            payload = json.loads(line).get("payload") or {}
        except Exception:
            continue
        if payload.get("rate_limits"):
            p5, p7 = _rates_from_payload(payload)
            if p5 is not None or p7 is not None:
                _ACCT["data"] = (p5, p7)
                break
    return _ACCT["data"]


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
