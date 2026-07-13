"""Cross-harness fleet title sidecars (stdlib only).

Canonical state:
  <state-root>/<harness>/<sid>.json
  {"title": str, "ts": float, "source": str, "offset": int}

``FLEET_TITLE_STATE_DIR`` overrides the state root. Otherwise the XDG state
location is used: ``${XDG_STATE_HOME:-~/.local/state}/agent-fleet/titles``.
The pre-F-21 Claude path (``~/.claude/.fleet-titles/<sid>.json``) remains a
read-only migration fallback; every new write goes to the neutral state root.
"""
import json
import os
import re
import tempfile
import time

_FRESH_SEC = 24 * 3600
_STALE_SWEEP_SEC = 7 * 24 * 3600
_SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _safe_key(value, label):
    value = str(value or "")
    if not value or not _SAFE_KEY_RE.match(value):
        raise ValueError("invalid %s" % label)
    return value


def state_root():
    explicit = os.environ.get("FLEET_TITLE_STATE_DIR")
    if explicit:
        return os.path.abspath(os.path.expanduser(explicit))
    xdg = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return os.path.join(xdg, "agent-fleet", "titles")


def titles_dir(harness="claude"):
    return os.path.join(state_root(), _safe_key(harness, "harness"))


def sidecar_path(sid, harness="claude"):
    return os.path.join(titles_dir(harness), _safe_key(sid, "session id") + ".json")


def lock_path(sid, harness="claude"):
    return os.path.join(titles_dir(harness), ".lock-" + _safe_key(sid, "session id"))


def _legacy_claude_path(sid):
    home = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    return os.path.join(home, ".fleet-titles", _safe_key(sid, "session id") + ".json")


def _read_path(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def read(sid, harness="claude", allow_legacy=True):
    """Return a sidecar dict or ``None``; malformed/missing state is harmless."""
    if not sid:
        return None
    data = _read_path(sidecar_path(sid, harness=harness))
    if data is not None:
        return data
    if allow_legacy and harness == "claude":
        return _read_path(_legacy_claude_path(sid))
    return None


def fresh_title(sid, now=None, max_age=_FRESH_SEC, harness="claude"):
    """Return a non-empty title only while the sidecar timestamp is fresh."""
    data = read(sid, harness=harness)
    if not data:
        return None
    ts = data.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    now = time.time() if now is None else now
    if now - ts > max_age:
        return None
    title = data.get("title")
    return title if isinstance(title, str) and title.strip() else None


def write(sid, title, source="refresher", offset=0, now=None, harness="claude"):
    """Atomically write neutral fleet-owned state. ``title=''`` is allowed."""
    data = {
        "title": title or "",
        "ts": time.time() if now is None else now,
        "source": source,
        "offset": int(offset),
    }
    directory = titles_dir(harness)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=directory, prefix="." + _safe_key(sid, "session id"), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, sidecar_path(sid, harness=harness))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return False
    return True


def sweep(now=None, max_age=_STALE_SWEEP_SEC):
    """Delete stale neutral sidecars/temp files across harness namespaces."""
    now = time.time() if now is None else now
    removed = 0
    try:
        harnesses = os.listdir(state_root())
    except OSError:
        return 0
    for harness in harnesses:
        directory = os.path.join(state_root(), harness)
        if not os.path.isdir(directory):
            continue
        try:
            names = os.listdir(directory)
        except OSError:
            continue
        for name in names:
            if not (name.endswith(".json") or name.endswith(".tmp")):
                continue
            path = os.path.join(directory, name)
            try:
                if now - os.path.getmtime(path) > max_age:
                    os.unlink(path)
                    removed += 1
            except OSError:
                pass
    return removed
