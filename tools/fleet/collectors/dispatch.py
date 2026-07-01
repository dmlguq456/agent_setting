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
import json
import os
import re
import time
from datetime import datetime, timezone

from ..model import DispatchJob, etime_to_min
from . import procscan

_AUTOPILOT = re.compile(r"/autopilot-([a-z-]+)")
_LOOPS = re.compile(r"loops/(oncall|note|study|drill)")
_MODE = re.compile(r"--mode ([a-z]+)")
_QA = re.compile(r"--qa ([a-z]+)")
# Valid qa levels — guards argv layer-1 (effective_qa) against contaminated matches:
# `\w+` is Unicode so `--qa (\w+)` would capture Korean/label text that merely mentions
# "--qa" inside a task description (e.g. "분사 시 --qa 없으면 …"). Narrowing to [a-z]+ AND
# filtering to real levels keeps the argv layer trustworthy, so the R3 layered resolver
# only falls through to jobs.log/plan/default when argv genuinely has no --qa.
_QA_LEVELS = ("quick", "light", "standard", "thorough", "adversarial")
_PIPE = re.compile(r"\s*([A-Za-z][\w-]*)(?::(\w+))?")
_SHELLS = ("zsh", "bash", "sh", "dash")


def _parse_pipe(pipe):
    """Parse a jobs.log pipe field, dual-form → (name, mode, qa).

    OLD form: `autopilot-code:dev(agent-fleet-dashboard)` (name:mode).
    NEW form: `capability=autopilot-code,mode=dev,qa=quick(round-3 x)` (key=val,... list
    before the first `(`). Distinguished by whether `=` appears before any `:` in the
    leading (pre-`(`) segment. name has any `autopilot-` prefix stripped either way.
    Parse failure → (None, None, None) — caller applies its own name fallback (repo or "job").
    """
    head = pipe.split("(", 1)[0] if pipe else ""
    eq_pos = head.find("=")
    colon_pos = head.find(":")
    if eq_pos != -1 and (colon_pos == -1 or eq_pos < colon_pos):
        # NEW form: leading key=val,... list.
        fields = {}
        for part in head.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                fields[k.strip()] = v.strip()
        name = fields.get("capability")
        if name and name.startswith("autopilot-"):
            name = name[len("autopilot-"):]
        return name, fields.get("mode"), fields.get("qa")
    # OLD form: name:mode via _PIPE regex.
    m = _PIPE.match(pipe or "")
    if not m:
        return None, None, None
    name = m.group(1)
    if name and name.startswith("autopilot-"):
        name = name[len("autopilot-"):]
    return name, m.group(2), None


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


def _claude_job_model(pid_s):
    """A claude dispatch (claude -p) has its own session — resolve its model via
    sessions/<pid>.json → sessionId → .statusline/<sid>.json (same path as claude.py).
    None if the headless session hasn't emitted a statusline yet (falls back to parent's
    model at render). Forward-looking: lets per-dispatch model differ from the parent later."""
    home = _proj_home()
    try:
        with open(os.path.join(home, "sessions", "%s.json" % pid_s)) as f:
            sid = json.load(f).get("sessionId")
    except Exception:
        return None
    if not sid:
        return None
    try:
        with open(os.path.join(home, ".statusline", "%s.json" % sid)) as f:
            m = json.load(f).get("model") or {}
        return m.get("display_name") or m.get("id")
    except Exception:
        return None


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


def _find_plan_dir(jcwd, slug):
    """Locate the plans/*_<slug>/ folder for (jcwd, slug): exact `_<slug>` suffix match,
    else the folder with max hyphen-token overlap (skipping done folders). abs path or None.
    Extracted from live_stage (REFACTOR, behavior-preserving — see plan Step 1.3)."""
    if not jcwd or not slug:
        return None
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
            return None
        cand = [best]
    return os.path.join(base, cand[-1])


def live_stage(jcwd, slug, fallback):
    """Derive plan→exec→test→done from plans/*_<slug>/ artifacts; fallback = argv key."""
    if not jcwd or not slug:
        return fallback
    pd = _find_plan_dir(jcwd, slug)
    if not pd:
        return fallback
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


def _plan_qa(jcwd, slug):
    """Read qa_level: from the resolved plan dir's pipeline_state.yaml (or plan/plan.md
    frontmatter) via a small line scan. None on any miss."""
    pd = _find_plan_dir(jcwd, slug)
    if not pd:
        return None
    for relpath in ("pipeline_state.yaml", os.path.join("plan", "plan.md")):
        try:
            with open(os.path.join(pd, relpath), encoding="utf-8", errors="replace") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("qa_level:"):
                        return s.split(":", 1)[1].strip()
        except OSError:
            continue
    return None


_QA_DEFAULT = {
    "code": "thorough",
    "spec": "thorough",
    "research": "thorough",
    "draft": "thorough",
    "refine": "thorough",
    "lab": "light",
    "note": "light",
}


def effective_qa(argv_qa, pipe_qa, jcwd, slug, key):
    """Layered qa resolver, first-hit precedence: argv > jobslog(pipe) > plan artifact >
    CONVENTIONS default. Returns (qa, source) — source in argv|jobslog|plan|default|None."""
    if argv_qa:
        return argv_qa, "argv"
    if pipe_qa:
        return pipe_qa, "jobslog"
    v = _plan_qa(jcwd, slug)
    if v:
        return v, "plan"
    v = _QA_DEFAULT.get(key)
    if v:
        return v, "default"
    return None, None


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
            qa_hits = [q for q in _QA.findall(args) if q in _QA_LEVELS]
            qa = qa_hits[-1] if qa_hits else None
            slug = os.path.basename(jcwd.rstrip("/")) if jcwd else ""
            dkey = "%s:%s" % (key, slug)
            if dkey in seen:
                continue
            seen.add(dkey)
            env = procscan.read_environ(pid_s)
            parent_sid = env.get("CLAUDE_CODE_SESSION_ID")
            is_child = env.get("CLAUDE_CODE_CHILD_SESSION") == "1"
            q, qsrc = effective_qa(qa, None, jcwd, slug, key)
            jobs.append(DispatchJob(
                key=key, stage=live_stage(jcwd, slug, key), mode=mode, qa=q,
                elapsed_min=etime_to_min(etime), slug=slug, cwd=jcwd,
                parent_sid=parent_sid, is_child=is_child, qa_source=qsrc, source="proc",
                harness="claude", pid=int(pid_s) if pid_s.isdigit() else None,
                model=_claude_job_model(pid_s),
            ))
        elif loop:
            key = loop.group(1)
            if key in seen:
                continue
            seen.add(key)
            jobs.append(DispatchJob(
                key=key, stage=None, elapsed_min=etime_to_min(etime),
                slug=key, parent_sid=None, is_child=False, source="proc",
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
        pname, pmode, pqa = _parse_pipe(pipe or "")
        if not pname:
            pname = repo or "job"
        # _parse_pipe already strips any `autopilot-` prefix on a successful parse; this
        # covers the fallback-name path (parse failure) where pname = repo or "job".
        if pname.startswith("autopilot-"):
            pname = pname[len("autopilot-"):]   # normalize to proc key form (code/spec/…)
        cwd = worktree if worktree not in ("-", "(main-tree)") else ""
        q, qsrc = effective_qa(None, pqa, cwd, slug, pname)
        jobs.append(DispatchJob(
            key=pname, stage=status, mode=pmode, qa=q,
            elapsed_min=_iso_elapsed_min(ts), slug=slug or worktree or repo,
            cwd=cwd, parent_sid=None, is_child=False, qa_source=qsrc,
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
