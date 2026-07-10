"""Liveness → 4-state (herdr vocabulary) — PRD §7.

Signals: process kill(0) survival · orphan (deleted-cwd worktree) · newest transcript/DB mtime
(15-min stale window) · claude native status (idle/shell/busy).

Fleet sessions resolve to working / idle / stale / dead. `blocked` needs the herdr socket
(out of MVP scope) so it is never emitted; `done` applies to dispatch jobs, not live sessions.
"""
import os

# Session stale window = 48h. Interactive sessions idle for hours/days are still alive, not
# stale (15min was far too tight — user 2026-07-01). Dispatch JOBS keep their own tight 15min
# window in dispatch.py._job_liveness (a headless build silent >15min = genuine hang suspect).
STALE_MIN = 48 * 60


def _alive(pid):
    if not pid:
        return True
    if os.name == "nt":
        # Windows has no os.kill(pid, 0) semantics and no /proc — probe via OpenProcess.
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # QUERY_LIMITED_INFORMATION
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
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
