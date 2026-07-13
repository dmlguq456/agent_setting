"""Codex CLI enrichment — passive, read-only (01_tap_mechanics.md §2).

Codex writes no per-session status file; telemetry is recovered from the rollout jsonl:
  ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl
  · line 1  = session_meta  → payload.cwd (pid↔session match key)
  · last "token_count" event → payload.info.{last_token_usage, model_context_window}
      + payload.rate_limits.{primary,secondary}.used_percent
Model/effort default from ~/.codex/config.toml (top-level model / model_reasoning_effort).

context% mirrors codex's OWN formula (codex-rs protocol.rs, fetched 2026-07-02 — user: fleet 의
codex context 부정확): tokens_in_context_window() = LAST request's total_tokens, and
  used% = 100 - percent_of_context_window_remaining
        = round(100 * max(0, last.total_tokens - BASELINE) / (window - BASELINE)),
BASELINE_TOKENS = 12000 ("prompts, tools and space to call compact") subtracted from BOTH sides
so a fresh session reads 0% used exactly like the codex TUI's "100% context left".
(History: v1 used input_tokens/window — plausible but ~2x codex's number; the 2026-07-01
empirical note that rejected (input+cached)/window still holds, superseded by the source
formula. Cumulative total_token_usage is NOT context occupancy — it double-counts inputs.)

A per-tick cache (cwd → newest rollout path) is built from cheap line-1 reads of all rollouts
(≈200 files); the expensive last-token-count parse touches only a 64 KB tail of the matched file.
"""
import json
import os
import re
import time

# rollout filename tail: rollout-<ISO-ts>-<uuid>.jsonl
_SID_RE = re.compile(r"-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$")

_INDEX = {"ts": 0.0, "map": None}          # cwd → rollout paths (newest first)
_INDEX_TTL = 1.5
_FALLBACK_CLAIMS = {"ts": 0.0, "sids": set()}  # session ids assigned without a proc fd
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


def _rollout_meta(path):
    """Minimal session_meta payload for a rollout, or {} when it is unreadable."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            m = json.loads(f.readline())
        if m.get("type") == "session_meta":
            return m.get("payload") or {}
    except Exception:
        pass
    return {}


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
    files.sort(reverse=True)
    m = {}
    for _mt, p in files:
        cwd = _rollout_cwd(p)
        if cwd:
            m.setdefault(cwd, []).append(p)
    _INDEX.update(ts=now, map=m)
    return m


def _sid(path):
    match = _SID_RE.search(os.path.basename(path))
    return match.group(1) if match else None


def _is_subagent(meta):
    source = meta.get("source")
    return (
        source == "subagent"
        or (isinstance(source, dict) and "subagent" in source)
        or meta.get("originator") == "subagent"
        or meta.get("thread_source") == "subagent"
    )


def _proc_rollout(pid, cwd, home):
    """Return the rollout open by this process, preferring root/user over subagent."""
    candidates = []
    try:
        names = os.listdir("/proc/%s/fd" % pid)
    except OSError:
        return None
    sessions_root = os.path.realpath(os.path.join(home, "sessions")) + os.sep
    wanted_cwd = os.path.realpath(cwd)
    for name in names:
        try:
            path = os.readlink("/proc/%s/fd/%s" % (pid, name))
            if path.endswith(" (deleted)"):
                path = path[:-10]
        except OSError:
            continue
        real = os.path.realpath(path)
        if not real.startswith(sessions_root) or not _sid(real):
            continue
        meta = _rollout_meta(real)
        if os.path.realpath(meta.get("cwd") or "") != wanted_cwd:
            continue
        candidates.append((1 if _is_subagent(meta) else 0, real))
    return min(candidates, default=(None, None))[1]


def _session_created(meta):
    value = meta.get("timestamp")
    if not isinstance(value, str):
        return None
    try:
        return __import__("datetime").datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _fallback_rollout(sess, home):
    """Match an idle TUI only when exactly one unclaimed rollout fits its start time."""
    now = time.time()
    if now - _FALLBACK_CLAIMS["ts"] >= _INDEX_TTL:
        _FALLBACK_CLAIMS.update(ts=now, sids=set())
    process_started = now - max(0, sess.elapsed_min) * 60
    candidates = []
    for path in _index(home).get(sess.cwd, []):
        sid = _sid(path)
        if not sid or sid in _FALLBACK_CLAIMS["sids"]:
            continue
        created = _session_created(_rollout_meta(path))
        if created is not None and process_started - 300 <= created <= now + 300:
            candidates.append(path)
    if len(candidates) != 1:
        return None
    path = candidates[0]
    _FALLBACK_CLAIMS["sids"].add(_sid(path))
    return path


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


_BASELINE_TOKENS = 12000    # codex-rs protocol.rs BASELINE_TOKENS — see module docstring


def _apply_token_count(sess, line):
    # codex's own formula (protocol.rs percent_of_context_window_remaining, 2026-07-02):
    # used = max(0, last.total_tokens - BASELINE) over effective window (window - BASELINE).
    try:
        p = json.loads(line).get("payload") or {}
    except Exception:
        return
    info = p.get("info") or {}
    win = info.get("model_context_window")
    ltu = info.get("last_token_usage") or {}
    tot = ltu.get("total_tokens")                   # last request total ≈ tokens in context window
    if isinstance(tot, (int, float)):
        sess.tokens = int(tot)
        if isinstance(win, (int, float)) and win > _BASELINE_TOKENS:
            eff = win - _BASELINE_TOKENS
            used = max(0, tot - _BASELINE_TOKENS)
            sess.ctx_pct = min(99, round(100.0 * used / eff))
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
        w = rl.get(k) or {}
        v = w.get("used_percent")
        rs = w.get("reset_at")            # epoch seconds (probed 2026-07-02)
        return (round(v) if isinstance(v, (int, float)) else None,
                float(rs) if isinstance(rs, (int, float)) else None)

    (p5, rs5), (p7, rs7) = rp("primary_window"), rp("secondary_window")
    return (p5, p7, rs5, rs7) if (p5 is not None or p7 is not None) else None


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
                _ACCT["data"] = (p5, p7, None, None)   # rollout fallback: no reliable reset time
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
    path = _proc_rollout(sess.pid, sess.cwd, home) or _fallback_rollout(sess, home)
    if not path:
        return                                       # no matching rollout → telemetry stays '—'
    # app-server 는 이 codex 버전(client-server)에서 세션 본체다. 예전엔 companion 으로 보고
    # mtime=None 을 강제해 *모든* interactive codex 세션의 working 판정을 죽였다(2026-07-03 회귀).
    # 실측: app-server leaf 의 /proc/cwd 가 프로젝트 cwd 와 정확히 일치하므로, cwd 로 매칭된
    # A UUID comes only from an owned fd or a one-candidate fallback; one newest
    # cwd rollout must never be stamped on every live TUI sharing the repository.
    sess.session_id = _sid(path)
    try:
        sess.mtime = os.path.getmtime(path)
    except OSError:
        sess.mtime = None
    tc = _tail_token_count(path)
    if tc:
        _apply_token_count(sess, tc)
