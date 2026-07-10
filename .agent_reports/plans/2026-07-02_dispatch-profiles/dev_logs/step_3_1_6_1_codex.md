## adapters/codex/bin/dispatch-headless.py

### Change 1 — parser(): add `--profile`
**Decision:** Pure additive CLI flag per Step 3.1. Placed after `--require-hook-trust` (last existing optional arg) so no existing arg order/position changes. No callers to update — argparse namespace attribute `args.profile` is new and only read by code added in this same step.
**old:**
```python
    p.add_argument("--require-hook-trust", action="store_true")
    return p
```
**new:**
```python
    p.add_argument("--require-hook-trust", action="store_true")
    p.add_argument("--profile")
    return p
```

### Change 2 — append_job(): extend `pipe` with `profile=`
**Decision:** Preserves the existing `capability=,mode=,qa=` prefix and the `f.write(f"{ts}\topen\t{repo}\t{args.worktree}\t{args.slug}\t{pipe}\n")` line untouched (both required verbatim by plan Risks). `profile=` is appended only when `args.profile` is truthy, so profile-less dispatches produce a byte-identical pipe to before (DP-7 non-destructive).
**old:**
```python
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```
**new:**
```python
    pipe = f"capability={args.capability},mode={args.mode},qa={args.qa}"
    if args.profile:
        pipe += f",profile={args.profile}"
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
```

### Change 3 — main(): profile gate-first → create instance (anti-leak order)
**Decision:** Inserted strictly *after* the existing `check_runtime_projection(args.worktree, args.require_hook_trust)` gate (assertion literal preserved verbatim, line untouched) and *before* `agent_home = resolve_agent_home()`, matching plan order: `--check` gate first (no instance created on failure, `return 3` via `fail(...)`), then `--instance` create. `home_root`/`build_home` are derived from `resolve_agent_home()` (same marker-walk function already used elsewhere in the file — not the forbidden `Path(os.environ.get("AGENT_HOME", os.getcwd()))` anti-pattern). `profile_home` is declared once (`Path | None = None`, safe under `from __future__ import annotations`) right before the `if args.start:` block so it's always bound (avoids `NameError` at the later Popen site when `--profile` is omitted or action != start). Both `build-home.py` invocations pass through stdout/stderr on failure for operator visibility, mirroring the existing `check_runtime_projection` failure-reporting style. Considered reusing the later `agent_home = resolve_agent_home()` local instead of calling `resolve_agent_home()` again here, but that assignment sits after this block in the existing code and moving it up would be a structural reorder beyond the "pure extension" mandate — `resolve_agent_home()` is a pure/side-effect-free call, so invoking it twice is a strictly additive, zero-risk alternative.
**old:**
```python
    if args.start and shutil.which("codex") is None:
        return fail("codex-command-unavailable", 69, worktree=args.worktree)
    if args.start:
        rc = check_runtime_projection(args.worktree, args.require_hook_trust)
        if rc != 0:
            return rc

    agent_home = resolve_agent_home()
```
**new:**
```python
    if args.start and shutil.which("codex") is None:
        return fail("codex-command-unavailable", 69, worktree=args.worktree)
    profile_home: Path | None = None
    if args.start:
        rc = check_runtime_projection(args.worktree, args.require_hook_trust)
        if rc != 0:
            return rc
        if args.profile:
            home_root = resolve_agent_home() / ".dispatch" / "homes"
            build_home = resolve_agent_home() / "tools" / "profile" / "build-home.py"
            check_result = subprocess.run(
                ["python3", str(build_home), args.profile, "--check"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if check_result.returncode != 0:
                if check_result.stdout:
                    print(check_result.stdout, end="")
                if check_result.stderr:
                    print(check_result.stderr, end="", file=sys.stderr)
                return fail("invalid-dispatch-profile", 3, profile=args.profile)
            subprocess.run(
                ["python3", str(build_home), args.profile, "--instance", args.slug, "--home-root", str(home_root)],
                check=False,
            )
            profile_home = home_root / f"{args.slug}.{args.profile}"

    agent_home = resolve_agent_home()
```

### Change 4 — main(): Popen attach with `CODEX_HOME` (profile) vs current behavior (no profile)
**Decision:** When `profile_home` is set, `subprocess.Popen` gets `env={**os.environ, "CODEX_HOME": str(profile_home)}` — the dict spread inherits the full parent environment (required, per instruction: a bare `{"CODEX_HOME": ...}` dict would drop `PATH` and break the `sh -c "codex exec …"` exec). When no profile, the exact original `subprocess.Popen(["sh", "-c", command], start_new_session=True)` call is preserved unchanged (no `env=` kwarg at all — identical to current behavior, i.e. inherits parent env implicitly as before). Did not set `CLAUDE_CONFIG_DIR` here, per the plan's explicit cross-harness leakage warning.
**old:**
```python
    if action == "start":
        subprocess.Popen(["sh", "-c", command], start_new_session=True)
```
**new:**
```python
    if action == "start":
        if profile_home is not None:
            subprocess.Popen(["sh", "-c", command], start_new_session=True, env={**os.environ, "CODEX_HOME": str(profile_home)})
        else:
            subprocess.Popen(["sh", "-c", command], start_new_session=True)
```

### Change 5 — main(): report `profile=` in output
**Decision:** One-line addition to the existing `print(...)` block, matching the existing `key=value` reporting convention (`f"profile={args.profile or '-'}"` mirrors the `-` placeholder style used elsewhere for unset/optional fields in this family of tools). Placed right after `qa=` (the other dispatch-metadata field) and before the registry fields, keeping all pre-existing print lines and their order intact.
**old:**
```python
    print(f"qa={args.qa}")
    print(f"job_registry={jobs}")
```
**new:**
```python
    print(f"qa={args.qa}")
    print(f"profile={args.profile or '-'}")
    print(f"job_registry={jobs}")
```

---

## adapters/codex/bin/dispatch-harvest.py

### Change 1 — import `shutil`
**Decision:** Required for `shutil.rmtree` in Change 3. Inserted alphabetically between `import os` and `import sys`, consistent with the existing import ordering style in this file.
**old:**
```python
import argparse
from contextlib import contextmanager
import fcntl
import os
import sys
import tempfile
from pathlib import Path
```
**new:**
```python
import argparse
from contextlib import contextmanager
import fcntl
import os
import shutil
import sys
import tempfile
from pathlib import Path
```

### Change 2 — parser(): add `--keep-home`
**Decision:** Pure additive flag, `store_true` matching the sibling `--mark-done` flag's style, placed directly after it.
**old:**
```python
    p.add_argument("--mark-done", action="store_true")
    return p
```
**new:**
```python
    p.add_argument("--mark-done", action="store_true")
    p.add_argument("--keep-home", action="store_true")
    return p
```

### Change 3 — main(): collect + clean up profile instance homes on open→done transition
**Decision:** `homes_to_clean` is populated **only** inside the `if args.mark_done and fields[1] == "open":` branch — i.e. only for rows undergoing an actual open→done transition in this run — not from the `matched_jobs` snapshot (which also captures `running` rows under `--status all` and would otherwise risk `rmtree`-ing a live job's home; this was explicitly called out as Risk/round-1 fix #3 in the plan). `profile=` is parsed defensively from `fields[5]` (the pipe) by splitting on `,` and matching a `profile=` prefix — absent profile silently no-ops (backward-compatible with pre-existing profile-less rows). The home path is computed the same way `dispatch-headless.py` computes `profile_home` (`resolve_agent_home()/.dispatch/homes/<slug>.<profile>`), reusing the same `resolve_agent_home()` already defined in this file. Actual `shutil.rmtree(..., ignore_errors=True)` calls are deferred to *after* the jobs.log tempfile-atomic rewrite completes, so the registry state is durably updated before any filesystem cleanup runs (favors registry consistency over filesystem cleanliness if the process is interrupted mid-way). Each removal is additionally guarded by `home.exists()` per the instruction ("존재 시") even though `ignore_errors=True` would already no-op on a missing path — this makes the "only if it exists" intent explicit in code. `matches()`, the 6-field schema, `emit_header()`, `jobs_lock()`, and the tempfile atomic rewrite are untouched.
**old:**
```python
        original = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
        rewritten: list[str] = []
        matched_jobs: list[list[str]] = []
        matched = 0
        marked_done = 0
        malformed = 0

        for line in original:
            bare = line.rstrip("\n")
            fields = bare.split("\t")
            if len(fields) != 6:
                malformed += 1
                rewritten.append(line)
                continue
            if matches(args, fields):
                matched += 1
                matched_jobs.append(fields.copy())
                if args.mark_done and fields[1] == "open":
                    fields[1] = "done"
                    marked_done += 1
                    line = "\t".join(fields) + "\n"
            rewritten.append(line)

        if args.mark_done:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(jobs.parent), delete=False) as tmp:
                tmp.writelines(rewritten)
                tmp_name = tmp.name
            Path(tmp_name).replace(jobs)

        emit_header(args, jobs, matched, marked_done, malformed)
```
**new:**
```python
        original = jobs.read_text(encoding="utf-8").splitlines(keepends=True)
        rewritten: list[str] = []
        matched_jobs: list[list[str]] = []
        homes_to_clean: list[Path] = []
        matched = 0
        marked_done = 0
        malformed = 0

        for line in original:
            bare = line.rstrip("\n")
            fields = bare.split("\t")
            if len(fields) != 6:
                malformed += 1
                rewritten.append(line)
                continue
            if matches(args, fields):
                matched += 1
                matched_jobs.append(fields.copy())
                if args.mark_done and fields[1] == "open":
                    if not args.keep_home:
                        slug = fields[4]
                        profile_name = None
                        for part in fields[5].split(","):
                            if part.startswith("profile="):
                                profile_name = part[len("profile="):]
                                break
                        if profile_name:
                            homes_to_clean.append(resolve_agent_home() / ".dispatch" / "homes" / f"{slug}.{profile_name}")
                    fields[1] = "done"
                    marked_done += 1
                    line = "\t".join(fields) + "\n"
            rewritten.append(line)

        if args.mark_done:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(jobs.parent), delete=False) as tmp:
                tmp.writelines(rewritten)
                tmp_name = tmp.name
            Path(tmp_name).replace(jobs)

        for home in homes_to_clean:
            if home.exists():
                shutil.rmtree(home, ignore_errors=True)

        emit_header(args, jobs, matched, marked_done, malformed)
```

---

## Self-verification (required, run before this log was written)

Both commands below were run from repo root (`/home/Uihyeop/agent_setting-wt/dispatch-profiles`); all literals reported present (no `MISSING:` lines), and `ast.parse` succeeded for both files.

```
$ bash -c 'f=adapters/codex/bin/dispatch-headless.py; for s in "validate_dispatch_inputs" -- "--require-hook-trust" "check_runtime_projection(args.worktree, args.require_hook_trust)" "invalid-dispatch-capability" "invalid-dispatch-mode" "invalid-dispatch-qa" "quick,light,standard,thorough,adversarial" "Read adapters/codex/AGENTS.md first" "code-plan -> code-execute -> code-test -> code-report" "Autopilot-code execution contract" "Do not claim independent QA delegation" "Do not use adapters/claude" "fcntl.flock" "registry_lock={jobs}.lock"; do grep -Fq -- "$s" "$f" || echo "MISSING: $s"; done; echo done-headless'
done-headless

$ bash -c 'f=adapters/codex/bin/dispatch-harvest.py; for s in "fcntl.flock" "registry_lock={jobs}.lock"; do grep -Fq -- "$s" "$f" || echo "MISSING: $s"; done; echo done-harvest'
done-harvest

$ python3 -c "import ast; [ast.parse(open(f).read()) for f in ['adapters/codex/bin/dispatch-headless.py','adapters/codex/bin/dispatch-harvest.py']]"
AST_OK (no exception raised)
```

Extra sanity check (the `check_codex_bin_wrappers` marker-pattern assertion, L542-548 of `tools/check-adaptation-boundary.sh`) — also passed for both files:

```
$ for p in adapters/codex/bin/dispatch-headless.py adapters/codex/bin/dispatch-harvest.py; do
    grep -Fq 'def resolve_agent_home()' "$p" && grep -Fq 'core" / "CORE.md"' "$p" && ! grep -Fq 'Path(os.environ.get("AGENT_HOME", os.getcwd()))' "$p" && echo "OK: $p" || echo "FAIL: $p"
  done
OK: adapters/codex/bin/dispatch-headless.py
OK: adapters/codex/bin/dispatch-harvest.py
```

No `MISSING:`/`FAIL:` lines were emitted; all ~30 L599-630 boundary literals plus the L542-548 marker-pattern assertions survive unmodified. Full boundary-guard run (`bash tools/check-adaptation-boundary.sh`) is left to the orchestrator per instructions.
