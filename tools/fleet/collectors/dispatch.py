"""Dispatch section — per-project headless jobs, uncapped (PRD §4B, §6).

Two sources, merged:
  (a) process scan: Claude autopilot-*/loops jobs — the statusline job-scan logic ported
      verbatim EXCEPT the top-3 cap and the per-session related() cwd filter are removed
      (this is a global monitor, not a per-session statusline).
  (b) ~/.claude/.dispatch/jobs.log: tolerant merge. status ∈ {open, running} accepted
      (the live registry writes `running`, not `open` — §6 vocabulary gap); rows that are
      malformed (field count ≠ 6) are skipped and counted, never crash the reader.

codex/opencode headless dispatch appears ONLY via jobs.log (their argv has no /autopilot-,
01_tap §4d), so jobs.log rows not already covered by a live process are surfaced here.

live_stage() derives the real pipeline stage from plans/*_<slug>/ artifacts (ported from
statusline.sh:131-171) so the label reflects live progress, not the static argv.
"""
import os
import re
import time
from datetime import datetime, timezone

from ..model import DispatchJob, etime_to_min
from . import procscan

_AUTOPILOT = re.compile(r"/autopilot-([a-z-]+)")
_LOOPS = re.compile(r"loops/(oncall|note|study|drill)")
_MODE = re.compile(r"--mode (\w+)")
_QA = re.compile(r"--qa (\w+)")
_PIPE = re.compile(r"\s*([A-Za-z][\w-]*)(?::(\w+))?")
_SHELLS = ("zsh", "bash", "sh", "dash")


# --- jobs.log path ---
def _jobs_path(override=None):
    if override:
        return override
    env = os.environ.get("AGENT_DISPATCH_JOBS")
    if env:
        return env
    home = (os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
            or os.path.expanduser("~/.claude"))
    return os.path.join(home, ".dispatch", "jobs.log")


# --- job liveness = transcript mtime (dispatch-liveness.sh reuse, PRD §7) ---
def _proj_home():
    return (os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
            or os.path.expanduser("~/.claude"))


def _enc(path):
    return "".join("-" if ch in "/._" else ch for ch in path)


def _job_liveness(path, now, stale_min=15):
    """working (transcript ≤15min) / stale (hung) / dead (no transcript) / unknown (no path)."""
    if not path:
        return "unknown"
    proj = os.path.join(_proj_home(), "projects", _enc(path))
    newest = None
    try:
        for n in os.listdir(proj):
            if n.endswith(".jsonl"):
                m = os.path.getmtime(os.path.join(proj, n))
                if newest is None or m > newest:
                    newest = m
    except OSError:
        return "dead"
    if newest is None:
        return "dead"
    return "working" if (now - newest) / 60.0 <= stale_min else "stale"


# --- live_stage (ported statusline.sh:131-171) ---
def _has_entries(p):
    try:
        return any(True for _ in os.scandir(p))
    except OSError:
        return False


def live_stage(jcwd, slug, fallback):
    """Derive plan→exec→test→done from plans/*_<slug>/ artifacts; fallback = argv key."""
    if not jcwd or not slug:
        return fallback
    ar = ".agent_reports" if os.path.isdir(os.path.join(jcwd, ".agent_reports")) else ".claude_reports"
    base = os.path.join(jcwd, ar, "plans")
    try:
        cand = sorted(d for d in os.listdir(base) if d.endswith("_" + slug))
    except OSError:
        cand = []
    if not cand:
        # slug mismatch fallback: pick the plan folder with max hyphen-token overlap
        stoks = set(t for t in slug.split("-") if t)
        try:
            dirs = [d for d in os.listdir(base)
                    if not d.startswith(".") and os.path.isdir(os.path.join(base, d))]
        except OSError:
            dirs = []
        best, bestn, bestm = None, 0, -1.0
        for d in dirs:
            if os.path.exists(os.path.join(base, d, "pipeline_summary.md")):
                continue                      # skip done folders (avoid generic-token false "done")
            dslug = d.split("_", 1)[-1] if "_" in d else d
            n = len(stoks & set(t for t in dslug.split("-") if t))
            try:
                mt = os.path.getmtime(os.path.join(base, d))
            except OSError:
                mt = 0.0
            if n > bestn or (n == bestn and n > 0 and mt > bestm):
                best, bestn, bestm = d, n, mt
        if not best or bestn == 0:
            return fallback
        cand = [best]
    pd = os.path.join(base, cand[-1])
    if os.path.exists(os.path.join(pd, "pipeline_summary.md")):
        return "done"
    if _has_entries(os.path.join(pd, "test_logs")):
        return "test"
    if _has_entries(os.path.join(pd, "dev_logs")):
        return "exec"
    try:
        with open(os.path.join(pd, "plan", "checklist.md")) as f:
            if "[x]" in f.read().lower():
                return "exec"
    except OSError:
        pass
    if os.path.exists(os.path.join(pd, "plan", "plan.md")):
        return "plan"
    return "plan"


# --- source (a): process scan (uncapped, no related() filter) ---
def _scan_processes():
    jobs = []
    seen = set()
    for line in procscan._ps_lines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        pid_s, _comm, etime = parts[0], parts[1], parts[2]
        args = parts[3] if len(parts) > 3 else ""
        ms = _AUTOPILOT.findall(args)
        loop = _LOOPS.search(args)
        if ms and "claude" in args:
            if os.path.basename(args.split(None, 1)[0]) in _SHELLS:
                continue                      # launcher shell wrapper, not the claude process
            try:
                jcwd = os.readlink("/proc/%s/cwd" % pid_s)
            except OSError:
                jcwd = ""
            if jcwd.endswith(" (deleted)"):
                jcwd = jcwd[: -len(" (deleted)")]
            key = ms[-1]
            mode = (_MODE.findall(args) or [None])[-1]
            qa = (_QA.findall(args) or [None])[-1]
            slug = os.path.basename(jcwd.rstrip("/")) if jcwd else ""
            dkey = "%s:%s" % (key, slug)
            if dkey in seen:
                continue
            seen.add(dkey)
            jobs.append(DispatchJob(
                key=key, stage=live_stage(jcwd, slug, key), mode=mode, qa=qa,
                elapsed_min=etime_to_min(etime), slug=slug, cwd=jcwd, source="proc",
            ))
        elif loop:
            key = loop.group(1)
            if key in seen:
                continue
            seen.add(key)
            jobs.append(DispatchJob(
                key=key, stage=None, elapsed_min=etime_to_min(etime),
                slug=key, source="proc",
            ))
    return jobs


# --- source (b): jobs.log tolerant merge ---
def _iso_elapsed_min(ts):
    try:
        dt = datetime.fromisoformat(ts.strip())
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // 60))


def _scan_jobs_log(path, seen_slugs):
    jobs = []
    malformed = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            rows = f.read().splitlines()
    except OSError:
        return jobs, 0
    for line in rows:
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            malformed += 1
            continue
        ts, status, repo, worktree, slug, pipe = fields
        if status not in ("open", "running"):
            continue
        if slug in seen_slugs:
            continue                          # already shown as a live process job
        seen_slugs.add(slug)
        m = _PIPE.match(pipe or "")
        pname = m.group(1) if m else (repo or "job")
        pmode = m.group(2) if m else None
        if pname.startswith("autopilot-"):
            pname = pname[len("autopilot-"):]   # normalize to proc key form (code/spec/…)
        jobs.append(DispatchJob(
            key=pname, stage=status, mode=pmode, qa=None,
            elapsed_min=_iso_elapsed_min(ts), slug=slug or worktree or repo,
            cwd=worktree if worktree not in ("-", "(main-tree)") else "",
            source="jobs", status=status,
        ))
    return jobs, malformed


def collect(jobs_path=None, harness_filter=None):
    """Return merged [DispatchJob]. harness_filter does not restrict dispatch — the section
    is cross-harness by design (jobs, not sessions)."""
    proc_jobs = _scan_processes()
    seen = set(j.slug for j in proc_jobs if j.slug)
    log_jobs, malformed = _scan_jobs_log(_jobs_path(jobs_path), seen)
    jobs = proc_jobs + log_jobs
    now = time.time()
    for j in jobs:
        j.liveness = _job_liveness(j.cwd, now)
    # stash malformed count on the module for the render header (optional signal)
    collect.last_malformed = malformed
    return jobs


collect.last_malformed = 0
