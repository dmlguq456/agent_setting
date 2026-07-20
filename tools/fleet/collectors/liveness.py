"""Session liveness — evidence collection only. The verdict belongs to model.classify_session.

Signals gathered here: process survival re-verified against /proc start-time (PID-reuse
proof) · orphan (deleted-cwd worktree) · newest transcript/DB mtime · claude native status
(idle/shell/busy) · registry activity window (startedAt/updatedAt).

F-25: this module used to BE the classifier. It is now the tier-2/tier-3 input layer;
`classify()` keeps its signature and return contract (a state string) so callers do not
regress, but the decision itself moved to model.py's single classifier.

Fleet sessions resolve to working / idle / unused / stale / dead. `blocked` needs the
herdr socket (out of MVP scope) so it is never emitted; `done` applies to dispatch jobs.
"""
import os

from ..model import SESSION_STALE_MIN, classify_session

# Session stale window = 48h. Interactive sessions idle for hours/days are still alive, not
# stale (15min was far too tight — user 2026-07-01). Dispatch JOBS keep their own tight 15min
# window in dispatch.py._job_liveness (a headless build silent >15min = genuine hang suspect).
# Canonical value lives in model.SESSION_STALE_MIN; re-exported for existing callers.
STALE_MIN = SESSION_STALE_MIN


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


def _proc_evidence(pid, claimed_start=None, actual_start=None):
    """(alive, start_time_match) — tier-2 process facts.

    `claimed_start` = the registry's procStart; `actual_start` = /proc/<pid>/stat field 22
    read at scan time. Equal → the registry is talking about THIS process. Different → the
    pid was recycled and every registry claim about it belongs to a dead process.

    start_time_match is None when there is nothing to compare (no registry procStart, or
    /proc unreadable): absence of evidence is not evidence of mismatch, so the classifier
    treats None as "silent" and only False as a positive PID-reuse finding.
    """
    alive = _alive(pid)
    if not alive or not claimed_start:
        return alive, None
    if actual_start is None:
        from . import procscan
        actual_start = procscan.read_proc_start(pid)
    if actual_start is None:
        return alive, None
    return alive, str(actual_start) == str(claimed_start)


def _activity_ms(sess):
    """registry updatedAt - startedAt in ms — the §2.2 inactivity-history evidence.
    None when either endpoint is absent (fresh rows may carry neither → tolerate)."""
    started, updated = getattr(sess, "started_at", None), getattr(sess, "updated_at", None)
    if not isinstance(started, (int, float)) or not isinstance(updated, (int, float)):
        return None
    return max(0.0, (updated - started) * 1000.0)


def collect_evidence(sess):
    """Session → the evidence dict model.classify_session consumes."""
    actual = getattr(sess, "proc_start", None)
    alive, match = _proc_evidence(sess.pid, getattr(sess, "registry_proc_start", None), actual)
    return {
        "harness": sess.harness,
        "pid": sess.pid,
        "pid_alive": alive,
        "proc_start": actual,
        "proc_start_match": match,
        "orphan": bool(sess.orphan),
        "status": sess.status,
        "task_lifecycle": getattr(sess, "task_lifecycle", None),
        "mtime": sess.mtime,
        # `_has_transcript` is set by the claude enricher; other harnesses fall back to
        # "an mtime exists at all", which is the same signal they had pre-F-25.
        "transcript": bool(getattr(sess, "_has_transcript", sess.mtime is not None)),
        "started_at": getattr(sess, "started_at", None),
        "updated_at": getattr(sess, "updated_at", None),
        "activity_ms": _activity_ms(sess),
        "is_worker": bool(sess.is_child),
        "fd_owner": getattr(sess, "_fd_owner", None),
    }


def classify(sess, now, stale_min=STALE_MIN):
    """Session → state string. Signature/return preserved (collectors/__init__.py caller).

    Side effect: stamps `sess.state_evidence` with the classifier's reasoning so the
    verdict is auditable from `--json` without a second classification pass.
    """
    ev_in = collect_evidence(sess)
    key = ("s", sess.harness, sess.pid, ev_in.get("proc_start"))
    state, evidence = classify_session(ev_in, now, stale_min=stale_min, key=key)
    sess.state_evidence = evidence
    return state
