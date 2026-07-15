"""Codex CLI enrichment — passive, read-only (01_tap_mechanics.md §2).

Codex telemetry is recovered from the rollout jsonl, while the native task title is
read from the read-only ``threads.title`` state DB with ``session_index.jsonl``
(``id`` -> ``thread_name``) as a compatibility fallback:
  ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<sid>.jsonl
  · line 1  = session_meta  → payload.cwd (pid↔session match key)
  · last "token_count" event → payload.info.{last_token_usage, model_context_window}
      + payload.rate_limits.{primary,secondary}.used_percent and optional limit_window_seconds
Model/effort default from ~/.codex/config.toml (top-level model / model_reasoning_effort).

context% mirrors Codex's own formula: tokens_in_context_window() is the last
request's total_tokens, and
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
import sqlite3
import time
import urllib.request

from fleet.token_budget import parse_codex_token_count

# rollout filename tail: rollout-<ISO-ts>-<uuid>.jsonl
_SID_RE = re.compile(r"-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$")

_INDEX = {"ts": 0.0, "map": None}          # cwd → rollout paths (newest first)
_INDEX_TTL = 1.5
_FALLBACK_CLAIMS = {"ts": 0.0, "sids": set()}  # session ids assigned without a proc fd
_PROC_PATHS = {}                                  # pid -> rollout reserved at collect tick start
_CFG = {"ts": 0.0, "model": None, "effort": None}
_TITLE_INDEX = {"stamp": None, "map": {}}      # native state stamps -> sid: title


def _home():
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def _state_db(home):
    """Return the newest versioned Codex state DB without assuming one schema version."""
    candidates = []
    try:
        names = os.listdir(home)
    except OSError:
        return None
    for name in names:
        match = re.fullmatch(r"state_(\d+)\.sqlite", name)
        if match:
            candidates.append((int(match.group(1)), os.path.join(home, name)))
    return max(candidates, default=(None, None))[1]


def _file_stamp(path):
    if not path:
        return None
    try:
        st = os.stat(path)
        return st.st_mtime_ns, st.st_size
    except OSError:
        return None


def _thread_titles(home):
    """Tolerant Codex native-title index; state DB wins over the JSONL fallback."""
    index_path = os.path.join(home, "session_index.jsonl")
    db_path = _state_db(home)
    stamp = (
        _file_stamp(index_path),
        db_path,
        _file_stamp(db_path),
        _file_stamp(db_path + "-wal") if db_path else None,
    )
    if _TITLE_INDEX["stamp"] == stamp:
        return _TITLE_INDEX["map"]
    mapped = {}
    try:
        with open(index_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                sid = row.get("id") if isinstance(row, dict) else None
                name = row.get("thread_name") if isinstance(row, dict) else None
                if isinstance(sid, str) and isinstance(name, str) and name.strip():
                    mapped[sid] = name.strip()
    except OSError:
        pass
    if db_path:
        connection = None
        try:
            connection = sqlite3.connect("file:" + db_path + "?mode=ro", uri=True)
            for sid, title in connection.execute(
                "SELECT id, title FROM threads WHERE title IS NOT NULL AND title != ''"
            ):
                if isinstance(sid, str) and isinstance(title, str) and title.strip():
                    mapped[sid] = title.strip()
        except (OSError, sqlite3.Error):
            pass
        finally:
            if connection is not None:
                connection.close()
    _TITLE_INDEX.update(stamp=stamp, map=mapped)
    return mapped


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


def prepare_tick(sessions):
    """Reserve proc-owned rollouts before any same-cwd fallback attribution.

    A rollout can be visible only on a newer Codex process while an older TUI in
    the same cwd has no open transcript fd. Enrichment is PID-ordered, so without
    a prepass the older row can claim the newer process's sole fallback candidate
    and both rows display one session id/title. Reserve every owned fd first.
    """
    home = _home()
    paths = {}
    claimed = set()
    for sess in sessions:
        if getattr(sess, "harness", None) != "codex" or not getattr(sess, "cwd", None):
            continue
        path = _proc_rollout(sess.pid, sess.cwd, home)
        if not path:
            continue
        paths[sess.pid] = path
        sid = _sid(path)
        if sid:
            claimed.add(sid)
    _PROC_PATHS.clear()
    _PROC_PATHS.update(paths)
    _FALLBACK_CLAIMS.update(ts=time.time(), sids=claimed)


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
    # Shared parser keeps active context separate from cumulative session counters.
    telemetry = parse_codex_token_count(line, session_id=sess.session_id)
    sess.active_context_tokens = telemetry.active_context_tokens
    sess.context_window_tokens = telemetry.context_window_tokens
    sess.session_input_tokens = telemetry.session_input_tokens
    sess.session_cached_input_tokens = telemetry.session_cached_input_tokens
    sess.session_output_tokens = telemetry.session_output_tokens
    sess.session_reasoning_output_tokens = telemetry.session_reasoning_output_tokens
    sess.session_total_tokens = telemetry.session_total_tokens
    if telemetry.active_context_tokens is not None:
        # Legacy render compatibility: Codex ``tokens`` remains active context.
        sess.tokens = telemetry.active_context_tokens
    if telemetry.context_used_pct is not None:
        sess.ctx_pct = telemetry.context_used_pct
    try:
        p = json.loads(line).get("payload") or {}
    except Exception:
        return
    p5, p7, windows = _rates_from_payload(p)
    if p5 is not None:
        sess.rl_5h = p5
    if p7 is not None:
        sess.rl_7d = p7
    if windows:
        sess.rl_windows = windows


def _duration_label(seconds):
    """Human label for a Codex limit_window_seconds value.

    Incident 2026-07-13: Codex primary_window changed to 604800 seconds while fleet still
    hard-labeled primary as 5h. Known durations get stable labels; unknown durations are
    shown as their actual duration instead of being forced into the old 5h/7d schema.
    """
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return None
    seconds = int(seconds)
    known = {
        300 * 60: "5h",
        24 * 60 * 60: "24h",
        7 * 24 * 60 * 60: "7d",
        30 * 24 * 60 * 60: "30d",
    }
    if seconds in known:
        return known[seconds]
    if seconds % (7 * 24 * 60 * 60) == 0:
        return "%dw" % (seconds // (7 * 24 * 60 * 60))
    if seconds % (24 * 60 * 60) == 0:
        return "%dd" % (seconds // (24 * 60 * 60))
    if seconds % 3600 == 0:
        return "%dh" % (seconds // 3600)
    if seconds % 60 == 0:
        return "%dm" % (seconds // 60)
    return "%ds" % seconds


def _legacy_window_key(label):
    if label == "5h":
        return "rl_5h"
    if label == "7d":
        return "rl_7d"
    return None


def _window_from_limit(name, data, legacy_label):
    d = data or {}
    v = d.get("used_percent")
    if not isinstance(v, (int, float)):
        return None
    label = _duration_label(d.get("limit_window_seconds")) or legacy_label
    rs = d.get("reset_at")
    if not isinstance(rs, (int, float)):
        rs = d.get("resets_at")
    reset = float(rs) if isinstance(rs, (int, float)) else None
    return {"source": name, "label": label, "pct": round(v), "reset": reset}


def _rates_from_payload(p):
    """(rl_5h, rl_7d, windows) from a token_count payload, EXPIRY-AWARE.

    Legacy rollout payloads had primary/secondary windows that meant 5h/7d. Newer Codex
    payloads may include `limit_window_seconds`; that duration is now the label source.
    """
    rl = p.get("rate_limits") or {}

    windows = []
    legacy = {"rl_5h": None, "rl_7d": None}
    for source, fallback in (("primary", "5h"), ("secondary", "7d")):
        win = _window_from_limit(source, rl.get(source), fallback)
        if not win:
            continue
        if isinstance(win.get("reset"), (int, float)) and win["reset"] < time.time():
            win["pct"] = 0
        windows.append([win["label"], win["pct"], win.get("reset")])
        key = _legacy_window_key(win["label"])
        if key:
            legacy[key] = win["pct"]
    return legacy["rl_5h"], legacy["rl_7d"], windows


_ACCT = {"ts": 0.0, "data": None}


def _api_usage():
    """LIVE account usage via the same endpoint the codex TUI itself uses (`/wham/usage`,
    bundle: account/usage/read) — read-only GET with the user's own OAuth token from auth.json.
    Rollout samples update only when a session is used, so an active probe is
    the reliable primary source. Return None on any failure
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

    def rp(k, fallback):
        w = rl.get(k) or {}
        return _window_from_limit(k, w, fallback)

    raw_windows = [rp("primary_window", "5h"), rp("secondary_window", "7d")]
    windows = [[w["label"], w["pct"], w.get("reset")] for w in raw_windows if w]
    if not windows:
        return None
    p5 = p7 = rs5 = rs7 = None
    for label, pct, reset in windows:
        if label == "5h":
            p5, rs5 = pct, reset
        elif label == "7d":
            p7, rs7 = pct, reset
    return {"rl_5h": p5, "rl_7d": p7, "rs_5h": rs5, "rs_7d": rs7, "windows": windows}


def account_usage():
    """Account-level usage: live API first (see _api_usage), then the NEWEST on-disk
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
            p5, p7, windows = _rates_from_payload(payload)
            if windows:
                windows = [[lbl, pct, rs] for lbl, pct, rs in (windows or [])]
                _ACCT["data"] = {"rl_5h": p5, "rl_7d": p7, "rs_5h": None, "rs_7d": None,
                                  "windows": windows}   # rollout fallback: no reliable reset time
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
    path = _PROC_PATHS.get(sess.pid) or _proc_rollout(sess.pid, sess.cwd, home) or _fallback_rollout(sess, home)
    if not path:
        return                                       # no matching rollout → telemetry stays '—'
    # app-server is the session process in this client-server Codex version. Treating it as a
    # companion once cleared mtime and broke working-state detection. Its /proc/cwd matches the
    # project cwd, so cwd-matched
    # A UUID comes only from an owned fd or a one-candidate fallback; one newest
    # cwd rollout must never be stamped on every live TUI sharing the repository.
    sess.session_id = _sid(path)
    sess._transcript_path = path                 # ephemeral: live title scheduler, not --json
    if sess.session_id:
        from fleet import titles
        native_title = _thread_titles(home).get(sess.session_id)
        sidecar_title = titles.fresh_title(sess.session_id, harness="codex")
        sess.title = sidecar_title or native_title or sess.title
    try:
        sess.mtime = os.path.getmtime(path)
    except OSError:
        sess.mtime = None
    tc = _tail_token_count(path)
    if tc:
        _apply_token_count(sess, tc)
