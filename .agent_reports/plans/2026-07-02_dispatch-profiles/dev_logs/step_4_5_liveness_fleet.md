# Step 4.1 + 5.1~5.4 — liveness + fleet profile-aware (root files only)

Scope: `utilities/dispatch-liveness.sh` (4.1), `tools/fleet/model.py` (5.1),
`tools/fleet/collectors/dispatch.py` (5.2, 5.3), `tools/fleet/render.py` (5.4).
Mirrors (`adapters/claude/...`) are **not** touched here — orchestrator copies them (5.5).
All edits are additive/backward-compatible: `profile=`-less jobs take the pre-existing
code path unchanged.

## Step 4.1 — `utilities/dispatch-liveness.sh`

**Edit** (inside the `while` loop, right after `enc=...`):

old:
```sh
  enc=$(printf '%s' "${wt:-}" | sed 's#[/._]#-#g')
  dir="$PROJ/$enc"
  newest=$(ls -t "$dir"/*.jsonl 2>/dev/null | head -1)
```

new:
```sh
  enc=$(printf '%s' "${wt:-}" | sed 's#[/._]#-#g')
  name=""
  case "$pipe" in *profile=*) name=${pipe##*profile=}; name=${name%%,*};; esac
  if [ -n "$name" ]; then
    dir="$AGENT_HOME/.dispatch/homes/${slug}.${name}/projects/$enc"
  else
    dir="$PROJ/$enc"
  fi
  newest=$(ls -t "$dir"/*.jsonl 2>/dev/null | head -1)
```

**Decision:** none (routine, plan-literal). `name=""` reset happens every loop iteration
before the `case` match (per-row, not hoisted above the loop), so a prior row's `profile=`
can never leak into a later `profile=`-less row (plan Risk / round-1 QA fix #4). `exit 3`
semantics and the rest of the ALIVE/SUSPECT/DEAD logic below are untouched.

Verified: `bash -n utilities/dispatch-liveness.sh` — OK.

## Step 5.1 — `tools/fleet/model.py`

**Edit** (`DispatchJob` dataclass, next to the other `Optional` fields):

old:
```python
    source: str = "proc"                # proc | jobs
    status: Optional[str] = None        # raw jobs.log status (open/running/...)
    liveness: str = "unknown"
    branch: Optional[str] = None        # git branch override — demo fixtures; None = compute from cwd
```

new:
```python
    source: str = "proc"                # proc | jobs
    status: Optional[str] = None        # raw jobs.log status (open/running/...)
    liveness: str = "unknown"
    profile: Optional[str] = None       # dispatch profile name (masked config home) — None = main home
    branch: Optional[str] = None        # git branch override — demo fixtures; None = compute from cwd
```

**Decision:** none — default `None` renders as `—` per the model's existing None
convention, matching every other unset-optional field.

## Step 5.2 — `tools/fleet/collectors/dispatch.py` (`_parse_pipe` + backfill)

**Edit 1** — `_parse_pipe()` widened to a 4-tuple at all 3 return points (docstring + NEW
form + failure path + OLD form):

old:
```python
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
```

new:
```python
def _parse_pipe(pipe):
    """Parse a jobs.log pipe field, dual-form → (name, mode, qa, profile).

    OLD form: `autopilot-code:dev(agent-fleet-dashboard)` (name:mode).
    NEW form: `capability=autopilot-code,mode=dev,qa=quick,profile=lab-runner(round-3 x)`
    (key=val,... list before the first `(`). Distinguished by whether `=` appears before
    any `:` in the leading (pre-`(`) segment. name has any `autopilot-` prefix stripped
    either way. OLD form has no profile k=v, so profile is always None there.
    Parse failure → (None, None, None, None) — caller applies its own name fallback
    (repo or "job").
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
        return name, fields.get("mode"), fields.get("qa"), fields.get("profile")
    # OLD form: name:mode via _PIPE regex.
    m = _PIPE.match(pipe or "")
    if not m:
        return None, None, None, None
    name = m.group(1)
    if name and name.startswith("autopilot-"):
        name = name[len("autopilot-"):]
    return name, m.group(2), None, None
```

**Decision:** the failure-path return (`return None, None, None, None`) is the one an
empty/malformed pipe string actually hits (`_scan_jobs_log` calls `_parse_pipe(pipe or
"")`; an empty string fails the `_PIPE` regex). Leaving it a 3-tuple while the caller
unpacks 4 would raise `ValueError: not enough values to unpack` and crash the whole
fleet render — round-1 QA fix #2, carried exactly per plan.

**Edit 2** — sole caller `_scan_jobs_log()`, unpack widened + `profile=` wired into the
`DispatchJob`:

old:
```python
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
```

new:
```python
        pname, pmode, pqa, pprofile = _parse_pipe(pipe or "")
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
            source="jobs", status=status, profile=pprofile,
        ))
```

**Edit 3** — new `_jobs_log_fields()` helper (mode+profile backfill for proc jobs) +
`collect()` wiring, inserted directly above `collect()`:

old:
```python
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
```

new:
```python
def _jobs_log_fields(path):
    """{slug: (mode, profile)} from the latest jobs.log row per slug (last-occurrence-wins,
    mirrors the reconciliation in _scan_jobs_log). Tolerant: missing file / malformed rows
    (field count != 6) never raise — worst case an empty or partial map."""
    fields_by_slug = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            rows = f.read().splitlines()
    except OSError:
        return fields_by_slug
    for line in rows:
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        slug = fields[4]
        _pname, pmode, _pqa, pprofile = _parse_pipe(fields[5] or "")
        fields_by_slug[slug] = (pmode, pprofile)   # last occurrence wins (append order)
    return fields_by_slug


def collect(jobs_path=None, harness_filter=None):
    """Return merged [DispatchJob]. harness_filter does not restrict dispatch — the section
    is cross-harness by design (jobs, not sessions)."""
    proc_jobs = _scan_processes()
    seen = set(j.slug for j in proc_jobs if j.slug)
    path = _jobs_path(jobs_path)
    log_jobs, malformed = _scan_jobs_log(path, seen)
    jobs = proc_jobs + log_jobs
    # mode+profile backfill for proc jobs whose argv lacked --mode (mode=None is an
    # opportunistic fix, not spec-mandated; profile=None backfill IS spec §7-mandated —
    # a proc-scanned profile job has no argv signal for --profile at all).
    if any(j.mode is None or j.profile is None for j in proc_jobs):
        log_fields = _jobs_log_fields(path)
        for j in proc_jobs:
            if j.slug and (j.mode is None or j.profile is None):
                lm, lp = log_fields.get(j.slug, (None, None))
                if j.mode is None:
                    j.mode = lm
                if j.profile is None:
                    j.profile = lp
    now = time.time()
    for j in jobs:
        j.liveness = _job_liveness(j.cwd, now, profile=j.profile, slug=j.slug)
    # stash malformed count on the module for the render header (optional signal)
    collect.last_malformed = malformed
    return jobs
```

**Decision:** `_jobs_log_fields` deliberately reuses `_parse_pipe` (not a second parser)
so NEW/OLD-form and prefix-stripping stay in one place. The backfill loop only touches
`proc_jobs` (never `log_jobs`, which already came straight from the log) and only
overwrites a field that is still `None` after the proc scan, so a proc job's own argv
`--mode`/`--qa` always wins over the backfill — non-destructive per plan Memo 5 (mode
backfill is opportunistic, profile backfill is the spec §7-mandated part). Guarded by an
`any(...)` short-circuit so `_jobs_log_fields` (a full file read) is skipped entirely
when nothing needs backfilling.

## Step 5.3 — `tools/fleet/collectors/dispatch.py` (`_job_liveness` profile-aware)

**Edit** — signature widened + profile-aware transcript-dir resolution:

old:
```python
def _job_liveness(path, now, stale_min=15):
    """working (transcript ≤15min) / stale (hung) / dead (no transcript) / unknown (no path)."""
    if not path:
        return "unknown"
    proj = os.path.join(_proj_home(), "projects", _enc(path))
```

new:
```python
def _job_liveness(path, now, stale_min=15, profile=None, slug=None):
    """working (transcript ≤15min) / stale (hung) / dead (no transcript) / unknown (no path).

    profile-aware (isomorphic to dispatch-liveness.sh, spec §7): when `profile` is set
    (and `slug` available), the job's transcript is isolated under its masked config home
    (`.dispatch/homes/<slug>.<profile>/projects/<enc>`) rather than the main home's
    `projects/<enc>` — resolving against the wrong root would always false-DEAD a profile
    job. profile None (the pre-existing, profile-less job case) → unchanged path."""
    if not path:
        return "unknown"
    if profile and slug:
        proj = os.path.join(_proj_home(), ".dispatch", "homes", "%s.%s" % (slug, profile),
                             "projects", _enc(path))
    else:
        proj = os.path.join(_proj_home(), "projects", _enc(path))
```

(rest of the function — newest-mtime scan, working/stale/dead thresholds — unchanged.)

Caller update (inside `collect()`, same edit block as Step 5.2 Edit 3 above):

old: `j.liveness = _job_liveness(j.cwd, now)`
new: `j.liveness = _job_liveness(j.cwd, now, profile=j.profile, slug=j.slug)`

**Decision:** none beyond the plan — this is the fleet-side counterpart of Phase 4.1,
isomorphic but not redundant (two different readers of the same
`.dispatch/homes/*/projects/` scan root, per plan Risks). `profile is None` keeps the
exact pre-existing path so profile-less jobs are byte-for-byte unaffected.

## Step 5.4 — `tools/fleet/render.py` (`_mq_tag` profile segment)

**Edit 1** — `_mq_tag()` gains a `profile` kwarg and appends a `·<profile>` segment:

old:
```python
def _mq_tag(mode, qa_text, qa_key):
    """The `(mode · qa)` tag shown after a dispatch name (mode dim, qa in its rigor color, middle
    dot). Returns (segments, display_width). Empty (mode and qa both absent) → ([], 0)."""
    if not mode and not qa_text:
        return [], 0
    out = [(" (", "dim")]
    w = 2
    if mode:
        out.append((mode, "dim")); w += len(mode)
    if qa_text:
        if mode:
            out.append(("·", "dim")); w += 1        # flush middle dot (tighter than ' · ')
        out.append((qa_text, qa_key)); w += len(qa_text)
    out.append((")", "dim")); w += 1
    return out, w
```

new:
```python
def _mq_tag(mode, qa_text, qa_key, profile=None):
    """The `(mode · qa · profile)` tag shown after a dispatch name (mode dim, qa in its rigor
    color, profile dim, middle dot). Returns (segments, display_width). Empty (mode, qa_text
    and profile all absent) → ([], 0)."""
    if not mode and not qa_text and not profile:
        return [], 0
    out = [(" (", "dim")]
    w = 2
    has_prev = False
    if mode:
        out.append((mode, "dim")); w += len(mode)
        has_prev = True
    if qa_text:
        if has_prev:
            out.append(("·", "dim")); w += 1        # flush middle dot (tighter than ' · ')
        out.append((qa_text, qa_key)); w += len(qa_text)
        has_prev = True
    if profile:
        if has_prev:
            out.append(("·", "dim")); w += 1
        out.append((profile, "dim")); w += len(profile)
    out.append((")", "dim")); w += 1
    return out, w
```

**Decision:** switched the old `if mode:` middle-dot guard (before `qa_text`) to a
`has_prev` flag so the dot logic generalizes correctly to 3 possible segments (e.g. a
profile-only job with no mode/qa should not get a leading dot) — a small deviation from
the plan's literal "qa 세그먼트 뒤에 profile 있으면 append" wording, needed because `mode`
and `qa_text` can each independently be absent while `profile` is present. Behavior for
the pre-existing 2-segment case (mode/qa only, profile=None) is byte-identical to the old
function. Reused the existing "dim" color key for the profile text, per plan instruction.

**Edit 2** — sole caller `_dispatch_row()`:

old: `tag_segs, tagw = _mq_tag(j.mode, qa_text, qa_key)`
new: `tag_segs, tagw = _mq_tag(j.mode, qa_text, qa_key, profile=j.profile)`

## Verification run

```
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['tools/fleet/model.py','tools/fleet/collectors/dispatch.py','tools/fleet/render.py']]"
bash -n utilities/dispatch-liveness.sh
```
Both passed (syntax-only; no gate/boundary scripts run per instructions — those are
orchestrator-owned after mirrors land).

## Not done here (explicitly out of scope for this sub-task)

- No mirrors written under `adapters/claude/...` (Step 4.2 / 5.5) — orchestrator copies.
- No `tools/check-adaptation-boundary.sh` / `hooks/portable-guards.test.sh` /
  `build-manifest.py --check` run — plan Verification gates, orchestrator-owned.
