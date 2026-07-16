"""Dispatch section — per-project headless jobs, uncapped (PRD §4B, §6).

Two sources, merged:
  (a) process scan: Claude autopilot-*/loops jobs — the statusline job-scan logic ported
      verbatim EXCEPT the top-3 cap and the per-session related() cwd filter are removed
      (this is a global monitor, not a per-session statusline).
  (b) dispatch registries: the current neutral <agent-home> registry plus legacy
      ~/.claude/.dispatch/jobs.log when different. status ∈ {open, running} accepted;
      rows that are malformed (field count ≠ 6) are skipped and counted, never crash
      the reader.

codex/opencode headless dispatch appears ONLY via jobs.log (their argv has no /autopilot-,
01_tap §4d), so jobs.log rows not already covered by a live process are surfaced here.

live_stage() derives the real pipeline stage from plans/*_<slug>/ artifacts (ported from
statusline.sh:131-171) so the label reflects live progress, not the static argv.
"""
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone

from .. import model
from ..model import DispatchJob, etime_to_min
from . import procscan

_AUTOPILOT = re.compile(r"/autopilot-([a-z-]+)")
_LOOPS = re.compile(r"loops/(oncall|note|study|drill|runtime-watch)")
_LOOP_KEYS = ("oncall", "note", "study", "drill", "runtime-watch")
_DRILL_LOG_PATH = re.compile(r"(/[^\s'\";]*drill[^\s'\";]*\.log)")
_DRILL_CASE_LINE = re.compile(r"^▶\s+(.+?)\s+\(work=", re.MULTILINE)
_MODE = re.compile(r"--mode ([a-z]+)")
_QA = re.compile(r"--qa ([a-z]+)")
# Valid qa levels — guards argv layer-1 (effective_qa) against contaminated matches:
# `\w+` is Unicode so `--qa (\w+)` would capture Korean/label text that merely mentions
# ``--qa`` inside a task description. Narrowing to [a-z]+ and
# filtering to real levels keeps the argv layer trustworthy, so the R3 layered resolver
# only falls through to jobs.log/plan/default when argv genuinely has no --qa.
_QA_LEVELS = ("quick", "light", "standard", "thorough", "adversarial")
_PIPE = re.compile(r"\s*([A-Za-z][\w-]*)(?::(\w+))?")
_SHELLS = ("zsh", "bash", "sh", "dash")
_PIPE_TOK = re.compile(r"[,\s]+")
_DRILL_SLUG_RE = re.compile(r"^drill-[a-z]+-(.+)-\d{14}-\d+$")   # registry slug → case
_DRILL_CWD_COMP_RE = re.compile(r"^drill-(.+)-[^-]+$")           # /tmp/drill-<case>-<rand> component to case


def _drill_case_from_slug(slug):
    """Extract a case from registry slug ``drill-<adapter>-<case>-<ts>-<pid>``."""
    m = _DRILL_SLUG_RE.match(slug or "")
    return m.group(1) if m else None


def _drill_case_from_cwd(cwd):
    """Extract a case from a ``/tmp/drill-<case>-<rand>`` cwd component."""
    if not (cwd or "").startswith("/tmp/"):
        return None
    for comp in (cwd or "").split("/"):
        if comp.startswith("drill-"):
            m = _DRILL_CWD_COMP_RE.match(comp)
            if m:
                case = m.group(1)
                return case[len("growing_"):] if case.startswith("growing_") else case
    return None


def _strip_autopilot_prefix(name):
    if name and name.startswith("autopilot-"):
        return name[len("autopilot-"):]
    return name


def _parse_pipe_meta(pipe):
    """Parse jobs.log pipe metadata.

    The registry stays six tab fields for backward compatibility; depth/parent/intensity
    live in this sixth ``pipe`` field as optional ``key=value`` pairs. OLD form
    ``autopilot-code:dev(...)`` still returns name/mode only.
    """
    head = pipe.split("(", 1)[0] if pipe else ""
    eq_pos = head.find("=")
    colon_pos = head.find(":")
    if eq_pos != -1 and (colon_pos == -1 or eq_pos < colon_pos):
        # continuation tokenizer (SD-F4, 2026-07-09 wild fixture): the writer
        # (dispatch-headless.py:260) emits a closed key= vocabulary, but a value can itself
        # contain spaces (e.g. `model_role=deep maker`) — a naive `,`-only or whitespace-only
        # split breaks one of the two forms. Tokenize on `[,\s]+`; a token WITH `=` starts a
        # new (k, v) pair, a token WITHOUT `=` is a continuation that space-joins onto the
        # PREVIOUS pair's value. This assumes every real field is written as `key=value`
        # (never a bare value) — see plan R8/N2 — so a stray `=`-free token can only be a
        # continuation, never a new field.
        fields = {}
        last_key = None
        for tok in _PIPE_TOK.split(head):
            if not tok:
                continue
            if "=" in tok:
                k, v = tok.split("=", 1)
                k = k.strip()
                fields[k] = v.strip()
                last_key = k
            elif last_key is not None:
                fields[last_key] = fields[last_key] + " " + tok
        fields["_name"] = _strip_autopilot_prefix(fields.get("capability"))
        return fields
    m = _PIPE.match(pipe or "")
    if not m:
        return {}
    return {"_name": _strip_autopilot_prefix(m.group(1)), "mode": m.group(2)}


def _parse_pipe(pipe):
    """Parse a jobs.log pipe field, dual-form → (name, mode, qa, profile)."""
    fields = _parse_pipe_meta(pipe)
    return fields.get("_name"), fields.get("mode"), fields.get("qa"), fields.get("profile")


def _parse_depth(value):
    try:
        depth = int(value or 1)
    except (TypeError, ValueError):
        return 1
    return max(1, depth)


_KNOWN_HARNESSES = {"claude", "codex", "opencode"}


def _infer_harness(meta, slug=None):
    """Return dispatch runtime from explicit metadata or legacy model fields."""
    h = (meta.get("harness") or "").strip().lower()
    if h in _KNOWN_HARNESSES:
        return h
    if meta.get("reasoning") or meta.get("approval"):
        return "codex"
    if meta.get("variant") or meta.get("agent"):
        return "opencode"
    if meta.get("effort"):
        return "claude"
    s = slug or ""
    for h in _KNOWN_HARNESSES:
        if s.startswith(h + "-") or ("-" + h + "-") in s:
            return h
    return None


def _same_path(a, b):
    if not a or not b:
        return False
    return a == b or os.path.abspath(a) == os.path.abspath(b)


def _codex_home():
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def _codex_transcript_cwd(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"cwd"' not in line:
                    continue
                try:
                    payload = (json.loads(line).get("payload") or {})
                except Exception:
                    continue
                cwd = payload.get("cwd")
                if isinstance(cwd, str) and cwd:
                    return cwd
    except OSError:
        return None
    return None


def _codex_sessions_dir(profile=None, slug=None):
    if profile and slug:
        return os.path.join(_registry_home(), ".dispatch", "homes", "%s.%s" % (slug, profile), "sessions")
    return os.path.join(_codex_home(), "sessions")


def _codex_sessions_dirs(cwd, profile=None, slug=None):
    """Return every session store that can own this Codex dispatch.

    Nested Codex conductors commonly launch a stage worker with a worktree-local
    CODEX_HOME. The registry records the worktree but not that inherited environment,
    so inspect the deterministic local projection before the Fleet process' own home.
    Profile jobs remain isolated to their explicit profile home.
    """
    if profile and slug:
        return [_codex_sessions_dir(profile, slug)]

    candidates = []
    if cwd:
        candidates.append(os.path.join(cwd, ".dispatch", "codex-home", "sessions"))
    candidates.append(_codex_sessions_dir())

    result = []
    seen = set()
    for path in candidates:
        key = os.path.abspath(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _codex_job_liveness(cwd, now, stale_min=15, profile=None, slug=None):
    if not cwd:
        return "unknown"
    newest = None
    for sessions in _codex_sessions_dirs(cwd, profile, slug):
        try:
            for root, _dirs, names in os.walk(sessions):
                for name in names:
                    if not (name.startswith("rollout-") and name.endswith(".jsonl")):
                        continue
                    path = os.path.join(root, name)
                    if not _same_path(_codex_transcript_cwd(path) or "", cwd):
                        continue
                    mtime = os.path.getmtime(path)
                    if newest is None or mtime > newest:
                        newest = mtime
        except OSError:
            continue
    if newest is None:
        return "dead"
    return "working" if (now - newest) / 60.0 <= stale_min else "stale"


def _opencode_db():
    explicit = os.environ.get("OPENCODE_DB")
    if explicit:
        return explicit
    data_home = os.environ.get("OPENCODE_DATA_HOME")
    if data_home:
        return os.path.join(data_home, "opencode.db")
    return os.path.expanduser("~/.local/share/opencode/opencode.db")


def _opencode_to_seconds(ts):
    if ts is None:
        return 0.0
    return float(ts) / 1000.0 if ts > 10_000_000_000 else float(ts)


def _opencode_heartbeat_age(slug, now):
    if not slug:
        return None
    path = os.path.join(_registry_home(), ".dispatch", "logs", slug + ".heartbeat")
    try:
        return (now - os.path.getmtime(path)) / 60.0
    except OSError:
        return None


def _opencode_job_liveness(cwd, now, stale_min=15, slug=None):
    if not cwd:
        return "unknown"
    db = _opencode_db()
    if not os.path.exists(db):
        return "unknown"
    con = None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=1.0)
        rows = con.execute(
            """
            SELECT
              s.directory,
              MAX(
                s.time_updated,
                COALESCE((SELECT MAX(time_updated) FROM message WHERE session_id = s.id), 0),
                COALESCE((SELECT MAX(time_updated) FROM part WHERE session_id = s.id), 0),
                COALESCE((SELECT MAX(time_updated) FROM session_message WHERE session_id = s.id), 0),
                COALESCE((SELECT MAX(time_created) FROM session_input WHERE session_id = s.id), 0)
              ) AS last_updated
            FROM session s
            ORDER BY last_updated DESC
            """
        )
        newest = None
        for row in rows:
            if _same_path(row[0], cwd):
                newest = _opencode_to_seconds(row[1])
                break
    except Exception:
        newest = None
    finally:
        if con is not None:
            con.close()
    if newest:
        return "working" if (now - newest) / 60.0 <= stale_min else "stale"
    hb_age = _opencode_heartbeat_age(slug, now)
    if hb_age is not None and hb_age <= stale_min:
        return "working"
    return "dead"


# F-15c: an `open` registry row with no transcript yet, within this startup grace window,
# is genuinely "not started" (queued) rather than dead — past the window with still no
# transcript, it's dead. Canonical value lives in model.JOB_QUEUED_GRACE_MIN (F-25 removed
# the constant duplication); re-exported here for existing callers.
_QUEUED_GRACE_MIN = model.JOB_QUEUED_GRACE_MIN


def _job_transcript_signal(job, now):
    """tier-3 evidence only: what the transcript/rollout/db mtime says, per harness.
    Returns working | stale | dead | unknown. No judgment — that is classify_job's job."""
    if job.harness == "codex":
        return _codex_job_liveness(job.cwd, now, profile=job.profile, slug=job.slug)
    if job.harness == "opencode":
        return _opencode_job_liveness(job.cwd, now, slug=job.slug)
    return _job_liveness(job.cwd, now, profile=job.profile, slug=job.slug)


def _dispatch_liveness(job, now, track=True):
    """Job → state string. Signature/return preserved; the verdict now comes from the
    single F-25 classifier. Stamps `job.state_evidence` as a side effect.

    track=False skips the cross-tick tracker (and thus hysteresis): used when the call is
    only deriving EVIDENCE for another row, so a row that is about to be dropped never
    leaves a tracker entry behind.
    """
    is_loop = job.source == "proc" and job.key in _LOOP_KEYS
    pid_alive = None
    proc_start_match = None
    if job.pid is not None:
        proc_path = "/proc/%s" % job.pid
        pid_alive = os.path.exists(proc_path)
        if pid_alive and job.proc_start:
            observed_start = procscan.read_proc_start(job.pid)
            if observed_start is not None:
                proc_start_match = str(observed_start) == str(job.proc_start)
    ev_in = {
        "source": job.source,
        "key": job.key,
        "is_loop": is_loop,
        "harness": job.harness,
        "status": job.status,
        "elapsed_min": job.elapsed_min,
        "slug": job.slug,
        "pid": job.pid,
        "proc_start": job.proc_start,
        "pid_alive": pid_alive,
        "proc_start_match": proc_start_match,
        # A loop proc row is decided by tier-2 evidence; skip the mtime probe entirely
        # (it was never consulted on that path pre-F-25 either).
        "transcript": None if is_loop else _job_transcript_signal(job, now),
        "proc_liveness": getattr(job, "_proc_liveness", None),
    }
    state, evidence = model.classify_job(ev_in, now,
                                         key=("j", job.slug) if track else None)
    job.state_evidence = evidence
    return state


# --- jobs.log path ---
def _registry_home():
    """Canonical dispatch-registry home — reproduces utilities/agent-home.sh resolution
    (AGENT_HOME → CLAUDE_HOME → $HOME/agent_setting if a dir → ~/.claude). Holds
    .dispatch/jobs.log and .dispatch/homes/ (profile masked homes). Distinct from the
    runtime telemetry home (_proj_home). See core/OPERATIONS.md §5.10."""
    h = os.environ.get("AGENT_HOME") or os.environ.get("CLAUDE_HOME")
    if h:
        return h
    cand = os.path.expanduser("~/agent_setting")
    if os.path.isdir(cand):
        return cand
    return os.path.expanduser("~/.claude")


def _jobs_path(override=None):
    if override:
        return override
    env = os.environ.get("AGENT_DISPATCH_JOBS")
    if env:
        return env
    home = _registry_home()
    return os.path.join(home, ".dispatch", "jobs.log")


def _candidate_jobs_paths(override=None):
    """Dispatch registries to read, in precedence order.

    Explicit override/env means the caller intentionally selected one registry. The default
    path follows the neutral <agent-home> resolution, then adds legacy ~/.claude only when
    it is a distinct existing file. This keeps old long-running drill/Claude jobs visible
    during migration without duplicating rows for normal projected installs.
    """
    if override:
        return [override]
    env = os.environ.get("AGENT_DISPATCH_JOBS")
    if env:
        return [env]
    paths = [_jobs_path()]
    legacy = os.path.expanduser("~/.claude/.dispatch/jobs.log")
    if legacy and not _same_path(legacy, paths[0]) and os.path.exists(legacy):
        paths.append(legacy)
    result = []
    seen = set()
    for path in paths:
        key = os.path.realpath(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


# --- job liveness = transcript mtime (dispatch-liveness.sh reuse, PRD §7) ---
def _proj_home():
    """Runtime telemetry home (projects/sessions/.statusline) — Claude Code config dir.
    DISTINCT from the registry home (_registry_home): telemetry dirs live only here, not
    under agent_setting. CLAUDE_CONFIG_DIR override honored, else ~/.claude."""
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def _enc(path):
    return "".join("-" if ch in "/._" else ch for ch in path)


def _model_display(mid):
    """'claude-opus-4-8[1m]' → 'Opus 4.8' (family word + short dotted version; date/context
    suffixes like -20251001 / [1m] dropped)."""
    parts = mid.split("[", 1)[0].replace("claude-", "").split("-")
    fam = parts[0].capitalize()
    ver = ".".join(p for p in parts[1:] if p.isdigit() and len(p) <= 2)
    return fam + ((" " + ver) if ver else "")


def _claude_job_model(pid_s, jcwd=None):
    """A claude dispatch (claude -p) has its own session — resolve its model via
    sessions/<pid>.json → sessionId → .statusline/<sid>.json (same path as claude.py).
    HEADLESS sessions never render a statusline, so fall back to the transcript's own
    "model" field (assistant entries carry the real model id) — without this a dispatch
    launched with --model opus showed the PARENT's model (user 2026-07-02: main=Fable /
    dispatch-model policy remains observable through fleet)."""
    # Runtime-home only (accepted asymmetry, plan A5/R7): a profile(masked) headless job's
    # own sessions/.statusline live under its masked config home
    # (_registry_home()/.dispatch/homes/...), not here, so this lookup misses and degrades
    # to None while _job_liveness (which DOES branch on profile) stays correct. Deferred
    # fix recorded in R7.
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
        pass
    if not jcwd:
        return None
    path = os.path.join(home, "projects", _enc(jcwd), sid + ".jsonl")
    try:
        sz = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, sz - 65536))
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    ids = re.findall(r'"model":"(claude-[a-z0-9.\-]+)', data)
    return _model_display(ids[-1]) if ids else None


def _job_liveness(path, now, stale_min=15, profile=None, slug=None):
    """working (transcript ≤15min) / stale (hung) / dead (no transcript) / unknown (no path).

    profile-aware (isomorphic to dispatch-liveness.sh, spec §7): when `profile` is set
    (and `slug` available), the job's transcript is isolated under its masked config home
    (`.dispatch/homes/<slug>.<profile>/projects/<enc>`) under the REGISTRY home
    (`_registry_home()` — masked homes live under agent_setting/.dispatch/homes/, never
    under the runtime telemetry home), rather than the RUNTIME home's `projects/<enc>`
    (`_proj_home()`) used by the non-profile branch. Resolving the profile branch against
    the wrong root would always false-DEAD a profile job. profile None (the pre-existing,
    profile-less job case) → unchanged runtime-home path."""
    if not path:
        return "unknown"
    if profile and slug:
        proj = os.path.join(_registry_home(), ".dispatch", "homes", "%s.%s" % (slug, profile),
                             "projects", _enc(path))
    else:
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
        with os.scandir(p) as entries:
            return any(True for _ in entries)
    except OSError:
        return False


def _is_code_job(key=None, capability=None, worker_role=None):
    return (key or "").startswith("code") or (capability or "") == "autopilot-code" or (worker_role or "").startswith("code-")


def _find_plan_dir(jcwd, slug, key=None, capability=None, worker_role=None):
    """Locate the plans/*_<slug>/ folder for (jcwd, slug): exact `_<slug>` suffix match,
    else the folder with max hyphen-token overlap (skipping done folders). abs path or None.
    Extracted from live_stage (REFACTOR, behavior-preserving — see plan Step 1.3)."""
    if not _is_code_job(key, capability, worker_role) or not jcwd or not slug:
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


def live_stage(jcwd, slug, fallback, capability=None, worker_role=None):
    """Derive plan→exec→test→done from plans/*_<slug>/ artifacts; fallback = argv key."""
    if not jcwd or not slug:
        return fallback
    pd = _find_plan_dir(jcwd, slug, fallback, capability, worker_role)
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


def _plan_qa(jcwd, slug, key=None, capability=None, worker_role=None):
    """Read qa_level: from the resolved plan dir's pipeline_state.yaml (or plan/plan.md
    frontmatter) via a small line scan. None on any miss."""
    pd = _find_plan_dir(jcwd, slug, key, capability, worker_role)
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


def effective_qa(argv_qa, pipe_qa, jcwd, slug, key, capability=None, worker_role=None):
    """Layered qa resolver, first-hit precedence: argv > jobslog(pipe) > plan artifact >
    CONVENTIONS default. Returns (qa, source) — source in argv|jobslog|plan|default|None."""
    if argv_qa:
        return argv_qa, "argv"
    if pipe_qa:
        return pipe_qa, "jobslog"
    v = _plan_qa(jcwd, slug, key, capability, worker_role)
    if v:
        return v, "plan"
    v = _QA_DEFAULT.get(key)
    if v:
        return v, "default"
    return None, None


_STAGE_SUFFIX_RE = re.compile(r"-(?:code-)?(?:plan|exec|execute|test|report)$")


def _slug_stem(slug):
    """Strip a trailing depth-2 stage-role suffix (F-15c dedup key): 'fleet-ui-v2-execute'
    -> 'fleet-ui-v2', 'x-code-plan' -> 'x', 'already' unchanged. Display/matching helper
    only — never mutates DispatchJob.slug itself."""
    if not slug:
        return slug
    return _STAGE_SUFFIX_RE.sub("", slug)


def _norm_cwd(p):
    """Normalize a cwd for cross-source string-equality matching (B1/B2, R6): the jobs.log
    `worktree` field is writer-verbatim (dispatch-headless.py:append_job — no
    canonicalization), while a process cwd resolved via `/proc/<pid>/cwd` is already
    symlink-canonical. Both match sides must pass through this SAME helper (realpath) so a
    symlinked or trailing-slash worktree still reconciles against the live process cwd."""
    return os.path.realpath(p)


def _live_claude_cwds(exclude_pids):
    """{normalized_cwd: pid} for live `claude -p` processes not already argv-matched.

    Targets tokenless headless dispatch (stdin-piped `claude -p < promptfile`, and
    session-limit `-p -c` resume — plan §5): argv carries no /autopilot- token, so
    `_scan_processes()` can never surface these as proc jobs. Gate: `comm == "claude"` AND
    an EXACT `-p` token in argv — token-equality via `args.split()` (`"-p" in args.split()`),
    never a substring test, so a `--print` long-form flag or an incidental "-p" inside the
    prompt body is rejected while interactive `claude --resume` sessions stay excluded too
    (R2). cwd is resolved via `os.readlink("/proc/<pid>/cwd")`, falling back to
    `sessions/<pid>.json`'s `cwd` field under the RUNTIME home (`_proj_home()`) if that
    fails (`_ps_lines()` carries no cwd column — procscan.py:53). Keys are normalized with
    `_norm_cwd` (os.path.realpath) so a symlinked/trailing-slash worktree still matches the
    jobs.log row (R6). Two live processes sharing one cwd → lowest pid wins, deterministic
    "earliest wins" (R3). Any per-process OS error is swallowed (skip that process); total
    scan failure (`_ps_lines()` → []) returns {}."""
    result = {}
    for line in procscan._ps_lines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        pid_s, comm = parts[0], parts[1]
        args = parts[3] if len(parts) > 3 else ""
        if comm != "claude":
            continue
        if "-p" not in args.split():
            continue
        if not pid_s.isdigit():
            continue
        pid = int(pid_s)
        if pid in exclude_pids:
            continue
        jcwd = None
        try:
            jcwd = os.readlink("/proc/%s/cwd" % pid_s)
            if jcwd.endswith(" (deleted)"):
                jcwd = jcwd[: -len(" (deleted)")]
        except OSError:
            try:
                with open(os.path.join(_proj_home(), "sessions", "%s.json" % pid_s)) as f:
                    jcwd = json.load(f).get("cwd")
            except Exception:
                jcwd = None
        if not jcwd:
            continue
        key = _norm_cwd(jcwd)
        if key not in result or pid < result[key]:
            result[key] = pid
    return result


def _drill_current_case_from_log(path):
    try:
        sz = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, sz - 65536))
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    matches = _DRILL_CASE_LINE.findall(data)
    if not matches:
        return None
    return matches[-1].strip().replace("growing:", "")


def _loop_current_case(args):
    for path in reversed(_DRILL_LOG_PATH.findall(args or "")):
        case_id = _drill_current_case_from_log(path)
        if case_id:
            return case_id
    return None


def _iso_to_epoch(ts):
    """ISO8601 jobs.log timestamp -> epoch seconds (float) | None. Sibling of
    `_iso_elapsed_min` (:806) but returns the raw instant instead of a pre-computed elapsed —
    route.py's `build_views` takes `now` as an argument (purity, §3.3), so the elapsed-minutes
    math for a route-node's `done` row happens there, not here."""
    try:
        dt = datetime.fromisoformat((ts or "").strip())
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _scan_route_nodes(paths):
    """{route_id: {node_id: {...}}} — F-28a (§3.3): unlike `_scan_jobs_log`, this pass keeps
    TERMINAL rows (done/killed/cancelled). A route node that just finished has no live job row
    left (`_scan_jobs_log` drops terminal rows before classification, dispatch.py:845-846), so
    without this separate pass a completed node could never render `✓` (plan §3.3's "설계상 가장
    놓치기 쉬운 지점"). Rereads the same jobs.log files (§3.2.3 — `_jobs_log_fields` precedent,
    not a new I/O pattern); last-occurrence-wins per (route_id, route_node), same reconciliation
    idiom as `_scan_jobs_log`'s per-slug dedup."""
    result = {}
    if isinstance(paths, (str, bytes, os.PathLike)):
        paths = [paths]
    for path in paths:
        path_result = {}
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                rows = f.read().splitlines()
        except OSError:
            continue
        for line in rows:
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) != 6:
                continue
            ts, status, _repo, _worktree, slug, pipe = fields
            meta = _parse_pipe_meta(pipe or "")
            route_id = meta.get("route_id")
            route_node = meta.get("route_node")
            if not route_id or not route_node:
                continue
            pid_s = meta.get("pid")
            path_result.setdefault(route_id, {})[route_node] = {
                "status": status, "slug": slug, "ts": _iso_to_epoch(ts),
                "pid": int(pid_s) if (pid_s or "").isdigit() else None,
                "harness": _infer_harness(meta, slug),
                "model": meta.get("model"),
                "effort": meta.get("effort") or meta.get("reasoning"),
                "completion_gate": meta.get("completion_gate"),
                "note": meta.get("note"),
                # code-test verification.md §10 — a route whose only surviving field trace is
                # a TERMINAL row (every carrying job already finished) still names its record's
                # path; without it here, route.resolve_records() has no way to find that record
                # once no LIVE job carries route_file anymore, and a fully-finished (or
                # stage-gap) route silently degrades despite its record being perfectly valid.
                "route_file": meta.get("route_file"),
                "route_hash": meta.get("route_hash"),
                # code-test verification_round_2.md §10 — same bug class, second location:
                # render.py's degrade-pool `covered_slugs` excludes a route's own depth-1
                # conductor from the degrade pool by matching a LIVE child's `parent_slug`. Once
                # that child goes terminal it vanishes from live `jobs` (same mechanism as
                # route_file above) and the conductor stops being excluded — its bare slug then
                # re-appears as a contradicting "no route record" card next to its own real
                # record card. `parent` (== `_scan_jobs_log`'s `parent_slug`, same pipe field,
                # already parsed) is the terminal-surviving half of that same fact.
                "parent": meta.get("parent") or meta.get("parent_slug"),
            }
        # Candidate paths are precedence-ordered (canonical first). Preserve
        # last-occurrence-wins inside each file, but never let a later legacy
        # registry overwrite canonical terminal evidence.
        for route_id, nodes in path_result.items():
            target = result.setdefault(route_id, {})
            for route_node, evidence in nodes.items():
                target.setdefault(route_node, evidence)
    return result


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
        env = procscan.read_environ(pid_s) if (ms or loop) else {}
        # Session-end distillers and Fleet title refreshers can inherit dispatch
        # metadata and even contain `/autopilot-*` as prompt data. They are support
        # workers, not dispatch jobs; procscan exposes them only through the dedicated
        # mem-worker path when `a` is enabled.
        if env.get("MEM_DISTILL") == "1" or env.get("FLEET_TITLE_REFRESH") == "1":
            continue
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
            parent_sid = env.get("AGENT_DISPATCH_PARENT_SESSION_ID") or env.get("CLAUDE_CODE_SESSION_ID")
            parent_slug = env.get("AGENT_DISPATCH_PARENT_SLUG")
            depth = _parse_depth(env.get("AGENT_DISPATCH_DEPTH"))
            is_child = env.get("AGENT_SESSION_ROLE", "").lower() == "worker" or env.get("CLAUDE_CODE_CHILD_SESSION") == "1" or bool(parent_slug or parent_sid)
            q, qsrc = effective_qa(qa, None, jcwd, slug, key)
            jobs.append(DispatchJob(
                key=key, stage=live_stage(jcwd, slug, key), mode=mode, qa=q,
                elapsed_min=etime_to_min(etime), slug=slug, cwd=jcwd,
                parent_sid=parent_sid, parent_slug=parent_slug, is_child=is_child,
                qa_source=qsrc, source="proc", harness="claude",
                pid=int(pid_s) if pid_s.isdigit() else None,
                proc_start=procscan.read_proc_start(pid_s) if pid_s.isdigit() else None,
                model=_claude_job_model(pid_s, jcwd), depth=depth,
                intensity=env.get("AGENT_DISPATCH_INTENSITY"),
                worker_role=env.get("AGENT_DISPATCH_WORKER_ROLE"),
                capability_owner=env.get("AGENT_DISPATCH_OWNER"),
                effort=env.get("AGENT_DISPATCH_EFFORT"),
                model_role=env.get("AGENT_DISPATCH_MODEL_ROLE"),
                route_file=env.get("AGENT_ROUTE_FILE") or None,
                route_id=env.get("AGENT_ROUTE_ID") or None,
                route_node=env.get("AGENT_ROUTE_NODE") or None,
                # AGENT_ROUTE_HASH is not exported by the headless launcher (§3.2.2) — a proc
                # job's route_hash stays None; integrity still rests on the record's own
                # recomputed hash (route.py P1), so this is not a weaker check.
            ))
        elif loop:
            key = loop.group(1)
            current_case = _loop_current_case(args)
            if current_case:
                dkey = "%s:%s" % (key, current_case)
            else:
                if any(k.startswith(key + ":") for k in seen):
                    continue
                dkey = key
            if dkey in seen:
                continue
            seen.add(dkey)
            try:
                jcwd = os.readlink("/proc/%s/cwd" % pid_s)
            except OSError:
                jcwd = ""
            if jcwd.endswith(" (deleted)"):
                jcwd = jcwd[: -len(" (deleted)")]
            parent_sid = env.get("AGENT_DISPATCH_PARENT_SESSION_ID") or env.get("CLAUDE_CODE_SESSION_ID")
            parent_slug = env.get("AGENT_DISPATCH_PARENT_SLUG")
            parent_cwd = env.get("AGENT_DISPATCH_PARENT_CWD") or (env.get("PWD") if parent_sid else None)
            is_child = env.get("AGENT_SESSION_ROLE", "").lower() == "worker" or env.get("CLAUDE_CODE_CHILD_SESSION") == "1" or bool(parent_slug or parent_sid)
            jobs.append(DispatchJob(
                key=key, stage="running", mode="loop/%s" % key,
                elapsed_min=etime_to_min(etime), slug=current_case or key, cwd=jcwd,
                parent_sid=parent_sid, parent_cwd=parent_cwd, parent_slug=parent_slug,
                is_child=is_child, source="proc", harness="claude" if env.get("CLAUDECODE") or "claude" in args else None,
                pid=int(pid_s) if pid_s.isdigit() else None,
                proc_start=procscan.read_proc_start(pid_s) if pid_s.isdigit() else None,
                worker_role=current_case,
                capability_owner=key,
                effort=env.get("AGENT_DISPATCH_EFFORT"),
                model_role=env.get("AGENT_DISPATCH_MODEL_ROLE"),
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


def _scan_jobs_log(path, seen_slugs, seen_keys=None, registry_priority=0):
    jobs = []
    malformed = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            rows = f.read().splitlines()
    except OSError:
        return jobs, 0
    # Reconcile each job to its LATEST row before deciding live-ness. Identity key = slug,
    # NOT the worktree path: a terminal (done/killed/cancelled) row drops the worktree to '-'
    # after harvest, so a path key would never match the earlier running row and the job would
    # zombie forever at its running timestamp. A slug appears running→done chronologically
    # (append order), so last-occurrence wins. (Bug: an `open/running`-first filter let a later
    # `done` never cancel the running row — 290h phantom jobs. User report 2026-07-01.)
    latest = {}
    order = []
    for registry_order, line in enumerate(rows):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            malformed += 1
            continue
        slug = fields[4]
        if slug not in latest:
            order.append(slug)
        latest[slug] = (registry_order, fields)  # last occurrence = newest status for this slug
    for slug in order:
        registry_order, fields = latest[slug]
        ts, status, repo, worktree, _slug, pipe = fields
        if status not in ("open", "running"):
            continue                          # newest state is terminal (done/killed/…) → not live
        cwd = worktree if worktree not in ("-", "(main-tree)") else ""
        if slug in seen_slugs:
            continue                          # already shown as a live process job
        # F-15c: (normalized cwd, slug-stem) dedup — a stage-worker registry row
        # (fleet-ui-v2-execute) reconciles against its already-shown proc job
        # (fleet-ui-v2) ONLY when both cwd and stem match; a different worktree (conductor
        # vs its own depth-2 child, OPERATIONS §5.10) never collapses, so both stay visible.
        if cwd and seen_keys and (_norm_cwd(cwd), _slug_stem(slug)) in seen_keys:
            continue
        seen_slugs.add(slug)
        meta = _parse_pipe_meta(pipe or "")
        pname = meta.get("_name") or repo or "job"
        # _parse_pipe_meta already strips any `autopilot-` prefix on a successful parse; this
        # covers the fallback-name path (parse failure) where pname = repo or "job".
        if pname.startswith("autopilot-"):
            pname = pname[len("autopilot-"):]   # normalize to proc key form (code/spec/…)
        capability = meta.get("capability")
        worker_role = meta.get("worker_role")
        q, qsrc = effective_qa(None, meta.get("qa"), cwd, slug, pname, capability, worker_role)
        parent_slug = meta.get("parent") or meta.get("parent_slug") or None
        parent_sid = meta.get("parent_sid") or meta.get("parent_session_id") or None
        parent_cwd = meta.get("parent_cwd") or meta.get("parent_worktree") or None
        harness = _infer_harness(meta, slug)
        pid_s = meta.get("pid")
        registry_pid = int(pid_s) if (pid_s or "").isdigit() else None
        jobs.append(DispatchJob(
            key=pname, stage=status, mode=meta.get("mode"), qa=q,
            elapsed_min=_iso_elapsed_min(ts), slug=slug or worktree or repo,
            cwd=cwd, parent_sid=parent_sid, parent_cwd=parent_cwd, parent_slug=parent_slug,
            is_child=bool(parent_slug or parent_sid or parent_cwd), qa_source=qsrc, source="jobs", status=status,
            harness=harness, model=meta.get("model"),
            pid=registry_pid, proc_start=meta.get("pid_start") or meta.get("proc_start"),
            profile=meta.get("profile"), depth=_parse_depth(meta.get("depth")),
            intensity=meta.get("intensity"), worker_role=worker_role,
            capability_owner=meta.get("owner") or meta.get("capability_owner"),
            effort=meta.get("effort"), model_role=meta.get("model_role"),
            route_file=meta.get("route_file"), route_id=meta.get("route_id"),
            route_hash=meta.get("route_hash"), route_node=meta.get("route_node"),
            attempt_id=meta.get("attempt_id"),
            registry_order=registry_order,
            registry_priority=registry_priority,
        ))
    return jobs, malformed


def _jobs_log_fields(paths):
    """{slug: (mode, profile)} from the latest jobs.log row per slug (last-occurrence-wins,
    mirrors the reconciliation in _scan_jobs_log). Tolerant: missing file / malformed rows
    (field count != 6) never raise — worst case an empty or partial map."""
    if isinstance(paths, (str, bytes, os.PathLike)):
        paths = [paths]
    fields_by_slug = {}
    for path in paths:
        path_fields = {}
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                rows = f.read().splitlines()
        except OSError:
            continue
        for line in rows:
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) != 6:
                continue
            slug = fields[4]
            _pname, pmode, _pqa, pprofile = _parse_pipe(fields[5] or "")
            path_fields[slug] = (pmode, pprofile)   # last occurrence wins within a file
        for slug, value in path_fields.items():
            if slug not in fields_by_slug:
                fields_by_slug[slug] = value         # first registry wins across files
    return fields_by_slug


def _reconcile_drill_rows(jobs, now=None):
    """Merge duplicate registry and process rows for the same drill run.

    Keep the registry row, absorb the process PID and its liveness as tier-2 EVIDENCE,
    and never write the registry.

    F-25: this used to overwrite `r.liveness` directly, which made it a second, competing
    classifier. It now stashes the proc row's state as `_proc_liveness` evidence and the
    single classifier (model.classify_job) decides — same outcome, one decision point.
    """
    # Index registry drill rows by validated case.
    reg_by_case = {}
    reg_by_runner_pid = {}
    for r in jobs:
        if r.source != "jobs":
            continue
        case = _drill_case_from_slug(r.slug)
        if not case:
            continue
        if _drill_case_from_cwd(r.cwd) != case:      # Validate the cwd case component.
            continue
        reg_by_case.setdefault(case, r)              # First registry row is canonical.
        pid_match = re.search(r"-(\d+)$", r.slug or "")
        if pid_match:
            reg_by_runner_pid.setdefault(int(pid_match.group(1)), r)
    if not reg_by_case:
        return jobs
    drop = set()
    for p in jobs:
        if p.source != "proc" or p.key != "drill":
            continue
        case = _drill_case_from_cwd(p.cwd) or p.worker_role or (p.slug if p.slug != "drill" else None)
        r = reg_by_case.get(case)
        if r is None and p.pid is not None:
            # run.sh itself runs from the harness worktree, not the fixture cwd,
            # so it may have no case signal. Registry slugs end in run.sh's $$;
            # use that exact PID to collapse the proc/control row deterministically.
            r = reg_by_runner_pid.get(p.pid)
        if r is None:
            continue
        # Absorb process PID and liveness into the canonical registry row as evidence.
        if r.pid is None:
            r.pid = p.pid
            r.proc_start = p.proc_start      # pid and its start-time travel together, always
        if r.elapsed_min is None:
            r.elapsed_min = p.elapsed_min
        # Reconciliation runs BEFORE the classify loop (so there is exactly one place a
        # liveness is assigned), which means a proc row normally has no state yet — derive
        # it here. A caller that already classified (or a test that pins one) is honored.
        pl = p.liveness
        if pl in (None, "unknown"):
            # track=False: this row is about to be dropped, so it must not occupy a
            # tracker slot (and its verdict is evidence, not a rendered state).
            pl = _dispatch_liveness(p, time.time() if now is None else now, track=False)
        if pl in ("working", "idle"):
            r._proc_liveness = pl                    # tier-2 evidence; classify_job weighs it
        drop.add(id(p))
    if not drop:
        return jobs
    return [j for j in jobs if id(j) not in drop]


def collect(jobs_path=None, harness_filter=None):
    """Return merged [DispatchJob]. harness_filter does not restrict dispatch — the section
    is cross-harness by design (jobs, not sessions)."""
    proc_jobs = _scan_processes()
    seen = set(j.slug for j in proc_jobs if j.slug)
    seen_keys = set((_norm_cwd(j.cwd), _slug_stem(j.slug)) for j in proc_jobs if j.cwd and j.slug)
    paths = _candidate_jobs_paths(jobs_path)
    log_jobs = []
    malformed = 0
    for registry_priority, path in enumerate(paths):
        path_jobs, path_malformed = _scan_jobs_log(
            path, seen, seen_keys, registry_priority=registry_priority
        )
        log_jobs.extend(path_jobs)
        malformed += path_malformed
    jobs = proc_jobs + log_jobs
    # mode+profile backfill for proc jobs whose argv lacked --mode (mode=None is an
    # opportunistic fix, not spec-mandated; profile=None backfill IS spec §7-mandated —
    # a proc-scanned profile job has no argv signal for --profile at all).
    if any(j.mode is None or j.profile is None for j in proc_jobs):
        log_fields = _jobs_log_fields(paths)
        for j in proc_jobs:
            if j.slug and (j.mode is None or j.profile is None):
                lm, lp = log_fields.get(j.slug, (None, None))
                if j.mode is None:
                    j.mode = lm
                if j.profile is None:
                    j.profile = lp
    # cwd-fallback enrichment for tokenless headless dispatch (stdin-piped `claude -p`,
    # `-p -c` resume — plan Phase B): these jobs.log rows have harness=None because their
    # argv carries no /autopilot- token, so _scan_processes() never argv-matched them.
    # Additive only — enriches log_jobs whose harness is still None (disjoint from the
    # mode+profile backfill above, which touches proc_jobs), so already-argv-matched proc
    # jobs are never affected. Order-independent w.r.t. the liveness loop below (j.cwd /
    # j.profile, which liveness reads, are unchanged by this block).
    # Guard the extra `ps` spawn: only scan for live processes when there is at least one
    # unenriched log job to match (fleet re-collects every ~2s, so skipping the second `ps`
    # when nothing needs it saves a subprocess per tick in the common all-argv-matched case).
    candidates = [j for j in log_jobs if j.harness is None and j.cwd]
    if candidates:
        exclude = {j.pid for j in proc_jobs if j.pid}
        cwd_index = _live_claude_cwds(exclude)
        consumed = set()
        for j in candidates:
            pid = cwd_index.get(_norm_cwd(j.cwd))
            if pid and pid not in consumed:
                j.harness = "claude"
                j.pid = pid
                j.proc_start = procscan.read_proc_start(pid)   # identity, not just a number
                consumed.add(pid)
                j.model = _claude_job_model(str(pid), j.cwd)
                j.stage = live_stage(j.cwd, j.slug, j.key, j.capability_owner, j.worker_role)
    now = time.time()
    # F-18a correlation merges proc evidence onto canonical registry rows BEFORE
    # classification, so every row is decided exactly once, by the single classifier.
    jobs = _reconcile_drill_rows(jobs, now)
    for j in jobs:
        j.liveness = _dispatch_liveness(j, now)
    # F-15c(a): a registry-only row (source="jobs") that turns out to be genuinely working
    # re-derives its breadcrumb from the real plan artifacts instead of the raw jobs.log
    # status word ("open"/"running") — otherwise a live job with real progress shows a
    # Avoid leaving a static queued/running placeholder forever.
    for j in jobs:
        if j.source == "jobs" and j.cwd and j.liveness == "working":
            j.stage = live_stage(j.cwd, j.slug, j.key, j.capability_owner, j.worker_role)
    # stash malformed count on the module for the render header (optional signal)
    collect.last_malformed = malformed
    # F-28a (§3.3) — terminal route-node evidence, stashed the same way `last_malformed` is
    # (module attribute, not a return-signature change — every existing caller stays untouched).
    try:
        collect.last_route_nodes = _scan_route_nodes(paths)
    except Exception:
        collect.last_route_nodes = {}
    return jobs


collect.last_malformed = 0
collect.last_route_nodes = {}
