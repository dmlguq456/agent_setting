"""Liveness → 4-state (herdr vocabulary) — PRD §7.

Signals: process kill(0) survival · orphan (deleted-cwd worktree) · newest transcript/DB mtime
(15-min stale window) · claude native status (idle/shell/busy).

Fleet sessions resolve to working / idle / stale / dead. `blocked` needs the herdr socket
(out of MVP scope) so it is never emitted; `done` applies to dispatch jobs, not live sessions.
"""
import os

STALE_MIN = 15


def _alive(pid):
    if not pid:
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                 # exists but not ours (shouldn't happen for own harnesses)
    except OSError:
        return False


def _from_status(status):
    if status == "busy":
        return "working"
    if status in ("idle", "shell"):
        return "idle"
    return None


def classify(sess, now, stale_min=STALE_MIN):
    # dead: process vanished between scan and classify (race) — the only 'dead' for a live scan
    if not _alive(sess.pid):
        return "dead"
    # orphan worktree: session lingering on a removed tree
    if sess.orphan:
        return "stale"
    m = sess.mtime
    if m is None:
        # process is alive but we have no transcript/DB signal → lean on claude status, else idle
        return _from_status(sess.status) or "idle"
    age_min = (now - m) / 60.0
    if age_min > stale_min:
        return "stale"
    # within the live window
    st = _from_status(sess.status)
    if st:
        return st
    # codex/opencode have no status field → recency heuristic (fresh write == working)
    return "working" if age_min < 1.0 else "idle"
