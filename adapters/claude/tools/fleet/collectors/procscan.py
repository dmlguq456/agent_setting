"""Universal backbone — enumerate every claude/codex/opencode session via the process table.

The only 100%-reliable tap (01_tap_mechanics.md §0): comm ∈ {claude,codex,opencode}
+ /proc/<pid>/cwd + ps etime. Per-harness collectors enrich these rows afterward;
a session's *existence* is decided here, never by enrichment success (PRD §1).

One matched process = one Session (a lingering broker on a deleted worktree is a real
process holding that cwd; the liveness layer paints it stale/dead — honest observation,
no fragile broker-vs-leaf heuristics).
"""
import os
import subprocess

from ..model import Session, etime_to_min

HARNESSES = ("claude", "codex", "opencode")
_DELETED = " (deleted)"


def _read_cwd(pid):
    """(resolved cwd, orphan?) — orphan = /proc/<pid>/cwd symlink ended in ' (deleted)'."""
    try:
        target = os.readlink("/proc/%d/cwd" % pid)
    except OSError:
        return "", False
    if target.endswith(_DELETED):
        return target[: -len(_DELETED)], True
    return target, False


def read_environ(pid):
    """/proc/<pid>/environ → dict[str,str] (or {} on failure). pid: int or str. Read-only, same-user only."""
    try:
        raw = open("/proc/%s/environ" % pid, "rb").read()
    except OSError:
        return {}
    env = {}
    for kv in raw.split(b"\0"):
        if b"=" in kv:
            k, v = kv.split(b"=", 1)
            env[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
    return env


def _ps_lines():
    # COLUMNS pinned huge: Claude Code injects terminal width into the statusline env and
    # ps truncates args= to COLUMNS, which would break argv matching downstream
    # (observed in statusline.sh:108). Harmless for procscan's comm match but kept for the shared
    # dispatch scan that reuses the same ps invocation contract.
    env = dict(os.environ, COLUMNS="100000")
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid=,comm=,etime=,args="],
            capture_output=True, text=True, timeout=5, env=env,
        ).stdout
    except Exception:
        return []
    return out.splitlines()


def _pid_ttys():
    """{pid: 'pts/N'} controlling tty per process (separate cheap ps so the main _ps_lines
    contract, shared with the dispatch scan, stays untouched). '?' (no tty) is kept as-is."""
    try:
        out = subprocess.run(["ps", "-eo", "pid=,tty="],
                             capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return {}
    m = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 2:
            try:
                m[int(p[0])] = p[1]
            except ValueError:
                pass
    return m


def _detached_ttys():
    """Set of ttys ('pts/N') whose tmux session has NO client attached. session_attached is
    per-session, so a session viewed in any window counts as attached. Empty if tmux absent."""
    try:
        out = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{pane_tty}\t#{session_attached}"],
            capture_output=True, text=True, timeout=2).stdout
    except Exception:
        return set()
    det = set()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].strip() == "0":
            det.add(parts[0].replace("/dev/", "", 1))
    return det


def _is_detached(tty, app_server, det_ttys):
    """A session no one is attached to — NOT tmux-specific (user 2026-07-02: sessions can just be
    run directly). Two general signals:
      · no controlling terminal (tty '?'/'-') → run in the background / detached from any terminal.
        (app-server companions ALSO have no tty but are services, not sessions → excluded.)
      · a tmux pane whose session has 0 attached clients → detached tmux session.
    A plain foreground terminal session keeps its pts and isn't in the tmux-detached set → attached."""
    if app_server:
        return False
    if not tty or tty in ("?", "-"):
        return True
    return tty in det_ttys


def _pid_alive(pid):
    """True if pid is a live process. Windows has no /proc: probe via OpenProcess."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _scan_disk(harness_filter=None):
    """Windows / no-procfs backbone: derive sessions from on-disk state instead of
    `ps -eo comm` + /proc (neither exists under MSYS). Claude writes one
    ~/.claude/sessions/<pid>.json per live session (sessionId, pid, cwd, status);
    presence + a live pid = an existing session. Per-harness collectors enrich as usual.
    Codex/opencode still surface via their own collectors; only claude has this native
    session-state file, so it is the one reconstructed here."""
    import glob
    import json
    from . import claude as _claude   # lazy: avoid procscan<->claude import cycle
    sessions = []
    if harness_filter and "claude" not in harness_filter:
        return sessions
    try:
        home = _claude._home()
    except Exception:
        return sessions
    for path in sorted(glob.glob(os.path.join(home, "sessions", "*.json"))):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            d = {}
        pid = d.get("pid")
        if not isinstance(pid, int):
            try:
                pid = int(os.path.splitext(os.path.basename(path))[0])
            except ValueError:
                continue
        if not _pid_alive(pid):
            continue
        cwd = (d.get("cwd") or "").replace("\\", "/")
        # NT has no /proc/<pid>/environ, so mem_worker safely remains false.
        sessions.append(Session(
            harness="claude",
            pid=pid,
            cwd=cwd,
            orphan=False,
            app_server=False,
            is_child=False,
            detached=False,
            elapsed_min=0,
            slug=os.path.basename(cwd.rstrip("/")) if cwd else None,
        ))
    return sessions


def scan(harness_filter=None):
    """Return [Session] for every live harness leaf process.

    harness_filter: optional iterable of harness names to keep (e.g. {'claude','codex'}).
    """
    if os.name == "nt":
        # Windows: MSYS `ps` has no -eo/comm and there is no /proc — reconstruct
        # session existence from on-disk state (see _scan_disk).
        return _scan_disk(harness_filter)
    sessions = []
    pid_tty = _pid_ttys()
    det_ttys = _detached_ttys()
    for line in _ps_lines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 3)          # pid, comm, etime, args
        if len(parts) < 3:
            continue
        pid_s, comm, etime = parts[0], parts[1], parts[2]
        args = parts[3] if len(parts) > 3 else ""
        if comm not in HARNESSES:
            continue
        if harness_filter and comm not in harness_filter:
            continue
        try:
            pid = int(pid_s)
        except ValueError:
            continue
        cwd, orphan = _read_cwd(pid)
        # app-server companion marker: codex-only, literal "app-server" token in args.
        # Interactive `codex`/`codex exec` never carries this token, so the gate cannot
        # false-positive on interactive sessions. COLUMNS is pinned to 100000 for the ps
        # call (see _ps_lines), so args are never truncated and the token stays visible
        # even for long command lines.
        app_server = comm == "codex" and "app-server" in args
        # Cross-runtime headless child marker (SD-24). Unreadable environ fails open:
        # a process is never hidden merely from argv/PPID/cwd resemblance.
        env = read_environ(pid)                       # Read once and reuse.
        is_child = bool(env.get("AGENT_DISPATCH_DEPTH")) or env.get("AGENT_DISPATCH_CHILD") == "1" or (
            comm == "claude" and env.get("CLAUDE_CODE_CHILD_SESSION") == "1"
        )
        # Tag memory workers and title refreshers to prevent inherited cwd/env misattribution.
        mem_worker = env.get("MEM_DISTILL") == "1" or env.get("FLEET_TITLE_REFRESH") == "1"
        detached = _is_detached(pid_tty.get(pid), app_server, det_ttys)
        sessions.append(Session(
            harness=comm,
            pid=pid,
            cwd=cwd,
            orphan=orphan,
            app_server=app_server,
            is_child=is_child,
            detached=detached,
            elapsed_min=etime_to_min(etime),
            slug=os.path.basename(cwd.rstrip("/")) if cwd else None,
            mem_worker=mem_worker,
        ))
    return sessions
