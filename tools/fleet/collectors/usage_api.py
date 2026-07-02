"""Account usage via the official OAuth endpoint — the same source as claude's /usage screen.

Why this exists (2026-07-02): per-model buckets ("Fable only" weekly limit) are visible in
/usage but are NOT written to any on-disk artifact the passive taps read — the statusline
stdin (v2.1.193/198) still ships only five_hour/seven_day, and stats-cache.json has no rate
data. The only source is `GET /api/oauth/usage` (bundle: "fetchUtilization"), so this is the
one deliberate exception to the disk-only observer rule: a READ-ONLY call with the user's own
token (identical to what the harness itself does), TTL-cached so the 2s render tick never
hammers the API. Failure of any kind → None → the usage bar falls back to the tap values.

Response shape (probed 2026-07-02): top-level five_hour/seven_day {utilization, resets_at}
plus a `limits[]` array — kind=session (5h) / weekly_all (7d) / weekly_scoped with
scope.model.display_name (e.g. "Fable") → the per-model bucket.
"""
import json
import os
import time
import urllib.request

_TTL = 60.0
_cache = {"ts": 0.0, "data": None}


def _home():
    return (os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
            or os.path.expanduser("~/.claude"))


def _token():
    try:
        with open(os.path.join(_home(), ".credentials.json")) as f:
            return (json.load(f).get("claudeAiOauth") or {}).get("accessToken")
    except Exception:
        return None


def _fetch():
    tok = _token()
    if not tok:
        return None
    req = urllib.request.Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={"Authorization": "Bearer " + tok,
                 "anthropic-beta": "oauth-2025-04-20",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.load(r)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    out = {"rl_5h": None, "rl_7d": None, "rl_ms": []}
    for lim in (d.get("limits") or []):
        if not isinstance(lim, dict) or not isinstance(lim.get("percent"), (int, float)):
            continue
        pct = round(lim["percent"])
        kind = lim.get("kind")
        if kind == "session":
            out["rl_5h"] = pct
        elif kind == "weekly_all":
            out["rl_7d"] = pct
        elif kind == "weekly_scoped":
            name = (((lim.get("scope") or {}).get("model") or {}).get("display_name")) or "model"
            lbl = name.split()[0].lower()
            if not any(x[0] == lbl for x in out["rl_ms"]):
                out["rl_ms"].append([lbl, pct])
    # fallback to the top-level objects if limits[] was missing/partial
    for key, fld in (("five_hour", "rl_5h"), ("seven_day", "rl_7d")):
        if out[fld] is None and isinstance((d.get(key) or {}).get("utilization"), (int, float)):
            out[fld] = round(d[key]["utilization"])
    if out["rl_5h"] is None and out["rl_7d"] is None and not out["rl_ms"]:
        return None
    return out


def account_usage():
    """TTL-cached account usage {rl_5h, rl_7d, rl_ms} for the claude account, or None."""
    now = time.time()
    if now - _cache["ts"] > _TTL:
        _cache["data"] = _fetch()
        _cache["ts"] = now              # failures cache too — no retry storm inside the TTL
    return _cache["data"]
