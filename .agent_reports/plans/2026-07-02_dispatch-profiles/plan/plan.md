---
status: done
created: 2026-07-02
qa_level: standard
---

# Dispatch Profiles — Implementation Plan

## Goal

Ship v1 (claude + codex) of the dispatch-profiles system from `spec/dispatch-profiles/prd.md`: per-dispatch masked config homes built by symlink partial-projection from a single repo source, declared as `profiles/<name>.yaml`, wired through the dispatch wrappers, and surfaced by the liveness/fleet monitoring tools — all non-destructive when `--profile` is omitted.

## Current State Analysis

Reference reading done: `spec/dispatch-profiles/prd.md` (DP-1..12 locked), and every port source / extension target below.

- **`adapters/codex/bin/dispatch-headless.py`** (279 L) — template for the new Claude wrapper. Structure: `parser()` (mutually-exclusive `--dry-run|--register|--start` + `--worktree/--slug/--capability/--mode/--qa/--prompt-file|--prompt-text/--jobs/--log-dir/--sandbox/--approval/--require-hook-trust`), `task_prompt()`, `qa_track()`, `dispatch_prompt()` (codex bootstrap prose), `shell_command()`, `jobs_lock()` (fcntl.flock contextmanager), `append_job()` (6-field row `ts\topen\trepo\twt\tslug\tpipe`, pipe=`capability=,mode=,qa=`), `resolve_agent_home()` (env AGENT_HOME with `core/CORE.md` marker, else `ROOT=parents[3]`), `check_runtime_projection()`, `validate_dispatch_inputs()`, `main()`. Default `jobs = agent_home/.dispatch/jobs.log`.
- **`adapters/codex/bin/install-runtime-projection.sh`** — `link()` primitive at L49-67: skips when target missing (`skip=… reason=projection-target-missing`), refuses to clobber a real non-symlink (except `hooks.json` which is backed up once), else `ln -sfn`. Per-skill / per-agent farm loops at L91-108. This `link()` semantics is the primitive `build-home.py` must reimplement in Python.
- **`adapters/codex/bin/dispatch-harvest.py`** (132 L) — `matches()` (6-field schema, status/slug/worktree selectors), `jobs_lock()`, `main()` rewrites jobs.log atomically via tempfile on `--mark-done`, prints `job_pipe=` per match. No home cleanup today.
- **`utilities/dispatch-liveness.sh`** (44 L) — reads `AGENT_HOME` via `agent-home.sh`, `PROJ="$AGENT_HOME/projects"`, per open row computes `enc=$(printf '%s' "$wt" | sed 's#[/._]#-#g')` and inspects `$PROJ/$enc/*.jsonl` mtime. `pipe` (6th field) is read but unused. Mirror at `adapters/claude/utilities/dispatch-liveness.sh`.
- **`tools/fleet/collectors/dispatch.py`** (384 L) — `_parse_pipe()` (dual-form OLD `name:mode` / NEW `key=val,…`; NEW form already ignores unknown k=v) returns `(name, mode, qa)`, called only at L351 in `_scan_jobs_log()`. `_scan_processes()` reads argv (`--mode`, `--qa`), builds `DispatchJob(harness="claude", …)`; jobs whose argv lacks `--mode` get `mode=None`. `_enc()`/`_job_liveness()` mirror the liveness path under `_proj_home()/projects/<enc>`. `collect()` merges proc + jobs.log.
- **`tools/fleet/model.py`** — `DispatchJob` dataclass (L143-166); no `profile` field yet.
- **`tools/fleet/render.py`** — `_mq_tag(mode, qa_text, qa_key)` at L442 (renders `(mode·qa)`), called only from `_dispatch_row()` at L483. `_NW_S` name-field width = 28 (L302).
- **`tools/check-adaptation-boundary.sh`** boundary rules:
  - `check_claude_tool_projection()` (~L2445): every path under `find tools -mindepth 1 ! -path '*/__pycache__*'` must have a concrete (non-symlink) counterpart at `adapters/claude/tools/<rel>`. → **new `tools/profile/build-home.py` and edited fleet files all require claude mirrors.**
  - `check_claude_utility_projection()` (~L2346): every file in `utilities/*` must have a concrete `adapters/claude/utilities/<name>`. → **`dispatch-liveness.sh` edit requires mirror sync.**
  - `check_codex_bin_wrappers()` (L525-548): codex bin files must be executable and use the `resolve_agent_home()` marker pattern (grep asserts `def resolve_agent_home()`, `core" / "CORE.md"`, and forbids `Path(os.environ.get("AGENT_HOME", os.getcwd()))`).
  - Codex dispatch assertions (L599-630): ~30 `grep -Fq` literals on `adapters/codex/bin/dispatch-headless.py` + the two `fcntl.flock` / `registry_lock={jobs}.lock` asserts on `dispatch-harvest.py`. **All must survive the edits.**
  - `check_claude_bin_wrappers()` (L1639-1653) does **not** enumerate required claude bin files (only `mem-distill-worker.sh`). → **new `adapters/claude/bin/dispatch-headless.py` needs no mirror and triggers no marker assertion, but should still follow the marker pattern and be `chmod +x`.**
- **`tools/build-manifest.py --check`** scans only `adapters/claude/skills/*`, `adapters/claude/agents/*`, `loops/README.md`, `settings.json`. → **`profiles/`, `tools/profile/`, new bin files do not affect the manifest.** PyYAML is already a dependency here (`import yaml` with graceful error), so `build-home.py` may use it identically.
- **`profiles/` is a deliberate repo-context build input (non-projection).** The new top-level `profiles/` catalog is intentionally NOT projected into any per-harness runtime setting dir (`claude_setting/`·`codex_setting/`·`opencode_setting/`) and is **not** added to the projection allowlist (`check_projection_entry_allowlist`). Rationale: the dispatch wrapper's `resolve_agent_home()` resolves via `Path(__file__).resolve()` to the source tree (repo root), so the build-home invoked by a dispatch reads *that tree's* `profiles/`. Unlike skills/agents/settings (runtime-first / repo-fallback divergence), `profiles/` is **repo-only** — it exists in the harness source tree that dispatch always runs from, so it never needs to appear under a runtime home.
- **`.gitignore`** — `.dispatch/` is ignored (line 75); generated homes never get committed.
- **Layout facts**: top-level `skills/<name>/` exists; root `agents/` is **forbidden** by `check_removed_root_surfaces()` (Claude agents live at `adapters/claude/agents/`). `core/` and `hooks/` exist at **both** repo root and runtime home root. **`settings.json` does NOT exist at repo root** — the canonical Claude settings file is `adapters/claude/settings.json` (build-manifest.py L223 reads it; projection allowlist L3002 projects it as the `settings.json` surface), and it exists at the runtime home (`~/.claude`) root only as a projection. So `settings.json` has the same runtime-first / repo-fallback divergence as skills/agents, not the both-roots availability of `core/`/`hooks/`. Fleet mirror tree confirmed at `adapters/claude/tools/fleet/{model.py,render.py,collectors/dispatch.py}`.

**AGENT_HOME resolution for `build-home.py` (critical):** codex wrappers use `ROOT = parents[3]`. `build-home.py` lives at two depths — `tools/profile/` (parents[2]=root) and `adapters/claude/tools/profile/` (parents[4]=root). A fixed `parents[N]` cannot serve a byte-identical mirror, so `build-home.py` **must marker-walk**: env-first (`AGENT_HOME` if `core/CORE.md` present) else walk `Path(__file__).resolve().parents` upward to the first dir containing `core/CORE.md`. The forbidden `Path(os.environ.get("AGENT_HOME", os.getcwd()))` anti-pattern must not appear.

## Change Plan

Phases are ordered by dependency. Within a phase, `[P]` marks steps parallelizable during execution. Every root-file change is paired with its mirror-sync step.

### Phase 0 — `profiles/` scaffolding (no dependencies)

> **`profiles/` placement note (non-projection, Memo 2).** All Phase 0 files live under the top-level `profiles/` catalog, which is a **repo-context-only build input** — it is not projected into any runtime setting dir and is not added to the projection allowlist. See the Current State bullet and Scope Notes. Do not add a projection surface entry for `profiles/`.

**Step 0.1** — NEW `profiles/README.md`. Catalog / main index: a table of `profile name | one-line description` (starts with the `lab-runner` row). Include a short section stating the DP-3 exception verbatim in intent: *"`profiles/` is top-level but harness-scoped — each declaration binds a `harness:` and concrete model names are the intended exception to the portable boundary rule, unlike `roles/`."* **Anchor the concrete-model exception to the canonical rule by name** — cite `core/ADAPTATION.md` (*"Concrete model names belong in adapter documents"*) as the governing rule, not as a derivation of `roles/README` (which is itself just an application of that rule). Summarize the L0/L1/L2 three-layer model (spec §2). **Add a one-line term-disambiguation note (Memo 4):** the dispatch **profile** here (`profiles/`, `--profile`, `profile=` k=v — a masked config home) is a *different concept* from the family's existing **mem-profile** (`mem profile <stem>`, DB `type=profile`, user personalization; `core/MEMORY.md §7.6`). State this explicitly in the README to prevent doc/grep/recall confusion. `[P]`

**Step 0.2** — NEW `profiles/templates/bootstrap-claude.md`. L0 reference stub for Claude workers: instructions to Read the four `core/` docs (CORE/CONVENTIONS/OPERATIONS/WORKFLOW), obey the guard hooks (**artifact-guard, git-state-guard, spec-gate (spec-skill-gate.sh), builtin-memory-guard** — matching the spec §5 guard set), an artifact-convention pointer (`.agent_reports/`), and the depth-1 rule (no re-dispatch). **No L1 orchestration section at all** (DP-10). Note the Claude attach mechanism (`CLAUDE_CONFIG_DIR`). `[P]`

**Step 0.3** — NEW `profiles/templates/bootstrap-codex.md`. Same L0 stub, Codex-flavored: name the same spec §5 guard set (**artifact-guard, git-state-guard, spec-gate, builtin-memory-guard**), mention `CODEX_HOME` + `AGENTS.md` attach, and that the worker still runs the codex preflight chain (the codex wrapper enforces it). No L1 section. `[P]`

**Step 0.4** — NEW `profiles/lab-runner.yaml`. Example declaration copied from spec §3 exactly: `name: lab-runner`, `description:`, `harness: claude`, `model_role: fast implementer`, `effort: medium`, `fragments: [profiles/fragments/lab-runner.md]`, `expose: {skills: [autopilot-lab, analyze-project, post-it], agents: [dev-team, qa-team, material-team], triggers: []}`. `[P]`

**Step 0.5** — NEW `profiles/fragments/lab-runner.md`. L2 specialization text: lab-runner role rules (autonomous experiment-runner discipline, RUNLOG conventions pointer, stay-in-lane guidance). `[P]`

### Phase 1 — `build-home.py` generator (depends on Phase 0)

**Step 1.1** — NEW `tools/profile/build-home.py`.
- CLI: `<name>` positional; `--instance <slug>`; `--check`; `--home-root` (default `<AGENT_HOME>/.dispatch/homes/`).
- `resolve_agent_home()`: env-first with `core/CORE.md` marker, else marker-walk up `Path(__file__).resolve().parents`. **Do not** use `Path(os.environ.get("AGENT_HOME", os.getcwd()))`.
- Declaration parse+validate (`import yaml`, graceful "PyYAML required" error like build-manifest): required fields `name`·`description`·`harness`; `harness ∈ {claude,codex,opencode}`; **`model_role` XOR `model`** (both-or-neither → error); `model` (concrete) valid only with a bound harness; validate `fragments` (list of existing paths) and `expose` schema (`skills`/`agents`/`triggers` lists).
- bootstrap assembly = read `profiles/templates/bootstrap-<harness>.md` + append each `fragments:` file in declared order — **plain concat, no transformation** — prefixed with header `<!-- generated-from: profiles/<name>.yaml — do not edit -->`.
  - **`harness: opencode` is a latent path in v1 (Memo 6c).** The schema accepts `harness ∈ {claude,codex,opencode}`, but v1 ships no `profiles/templates/bootstrap-opencode.md`, so an `opencode` declaration passes schema validation and then **fails loud at template-read with a clear error (exit 1)** ("missing template `profiles/templates/bootstrap-opencode.md`"). This is harmless in v1 (no opencode profile exists) but must fail-loud, never silently degrade — do not skip-on-missing the template.
- `--instance <slug>` build: create `<home-root>/<slug>.<name>/` and lay down a symlink farm using a Python port of the codex `link()` primitive (skip missing target; refuse to clobber a real non-symlink; else `os.symlink` after unlinking a prior symlink):
  - **L0 hard include (not surfaced in the declaration, DP-2) — harness-aware:**
    - **Always** (both harnesses): `core/` (whole dir) and `hooks/` (whole dir — all guard hooks). Both exist at repo root and runtime home root, so a plain `<HOME>/core`, `<HOME>/hooks` source is sufficient.
    - **harness=claude:** link the hook-registration load-bearing element `settings.json` via the **same runtime-first / repo-fallback dual path** used for skills/agents — first existing of `<HOME>/settings.json`, then `<HOME>/adapters/claude/settings.json`. (repo/worktree context has no root `settings.json`; without the fallback `link()` would skip-on-missing and silently drop it → guard hooks never register in the masked home, a silent DP-2 violation.)
    - **harness=codex:** do **NOT** link claude `settings.json` into a codex home (that would trip the spec §5 cross-harness leakage-refusal guard). Instead link the codex hook-registration file `hooks.json` via the dual path — first existing of `<HOME>/codex-hooks/hooks.json` (projection name — `codex_setting/codex-hooks` → `adapters/codex/hooks`), then `<HOME>/adapters/codex/hooks/hooks.json` (repo canonical; the source dir is `adapters/codex/hooks/`, **not** `codex-hooks/`).
    - Rationale: DP-2 ("guard hooks cannot be masked out") is satisfied by each harness's own hook-registration mechanism (claude = `settings.json`, codex = `hooks.json`). Because `link()` skip-on-missing only stays silent when *neither* dual-path source exists, the dual path covers both the repo and home contexts.
  - **expose subset:** for each `expose.skills` → `<instance>/skills/<name>` linked from the first existing of `<HOME>/skills/<name>`, `<HOME>/adapters/claude/skills/<name>`; for each `expose.agents` → `<instance>/agents/<name>.md` from the first existing of `<HOME>/agents/<name>.md`, `<HOME>/adapters/claude/agents/<name>.md`; triggers handled as declared (no-op when empty).
  - **credentials shared, not copied:** symlink `.credentials.json` into the instance (harness-owned, never duplicated/mutated).
  - **session state isolated:** never link `projects/`, `sessions/`, `.statusline/`, etc. — those stay inside the instance so transcript liveness is per-run clean.
  - write the assembled bootstrap to the instance's bootstrap filename (claude → `CLAUDE.md`, codex → `AGENTS.md`).
- `--check`: no writes; re-assemble bootstrap from the same inputs and compare against the deterministic expected content; also detect declaration parse errors / missing template / missing fragment. (No instance is created.)
- exit codes: `0` ok / `1` declaration or template error / `2` `--check` drift. **Never exit 3** (that code is wrapper-owned).
- Avoid hardcoded concrete runtime tokens (`claude -p`, `~/.claude`, model names) — resolve via env/AGENT_HOME so `warn_concrete_runtime_terms` does not gain WARNs.

**Step 1.2** — MIRROR: create byte-identical `adapters/claude/tools/profile/build-home.py` (concrete file, `chmod +x`). Byte-identity is required both by `check_claude_tool_projection` intent and because the marker-walk lets the same bytes work from both depths. `[pairs with 1.1]`

### Phase 2 — Claude dispatch wrapper (depends on Phase 1)

**Step 2.1** — NEW `adapters/claude/bin/dispatch-headless.py` (`chmod +x`). Port the codex wrapper structure: `parser()` with the same actions/args plus **`--profile <name>`**; `jobs_lock()` (fcntl.flock); `append_job()` writing the 6-field row; `resolve_agent_home()` marker-walk (env `AGENT_HOME` with `core/CORE.md`, else `parents[3]`); `main()` action branching.
- **jobs.log default + shared-registry ownership model:** `jobs = resolve_agent_home()/.dispatch/jobs.log`. Claude and codex share **one** AGENT_HOME (`~/.claude`) and therefore the **same `.dispatch/jobs.log` registry and the same `.dispatch/homes/` root** whenever AGENT_HOME resolves to `~/.claude`. This is what lets codex `dispatch-harvest.py` reclaim claude profile instance homes (Step 6.1): its cleanup hook is harness-agnostic and removes the home of every `profile=`-bearing `done` row, claude profiles included. (codex *may* pass `--jobs` to point at a repo-relative registry for non-profile runs, but **profile dispatch presumes the shared `~/.claude` registry** so harvest can see every row.) Add a comment stating this shared model — do **not** describe the two registries as a "deliberate difference," which would wrongly imply codex harvest cannot see claude rows. DP-4 ("removed at harvest") holds because both harnesses converge on the one registry.
- **`--start` + `--profile`:** gate-first, then create → register → launch (this order prevents an instance leak on gate failure — `--check` validates declaration/template re-assembly and needs no instance, so run it before creating anything):
  1. `build-home.py <name> --check` gate → on non-zero, `fail(...)` and `return 3` (no instance created yet, so no leak),
  2. `build-home.py <name> --instance <slug>` (create the ephemeral instance),
  3. `append_job(...)` (register the row *before* launch so harvest can always reclaim the home),
  4. `subprocess.Popen` `claude -p` with `env={**os.environ, "CLAUDE_CONFIG_DIR": "<home-root>/<slug>.<name>"}` (**must inherit `os.environ`** — a bare dict drops `PATH` and breaks the `claude` exec), `start_new_session=True`.
- **`--profile` omitted = current behavior** (main home, no instance, no gate) — non-destructive (DP-7).
- **pipe extension:** `pipe = f"capability={args.capability},mode={args.mode},qa={args.qa}"` and append `,profile={args.profile}` only when set → `capability=,mode=,qa=,profile=`.
- **worker prompt:** unlike codex, do **not** force a preflight chain — the `CLAUDE_CONFIG_DIR` masked home already loads the masked bootstrap. When a profile is set, keep the prompt minimal: task text + depth-1 reminder. AGENT_HOME resolution uses the marker-walk pattern (no anti-pattern).
- No mirror needed (adapter-specific; `check_claude_bin_wrappers` does not enumerate this file).

### Phase 3 — Codex dispatch wrapper `--profile` (depends on Phase 1; parallel with Phase 2)

**Step 3.1** — EDIT `adapters/codex/bin/dispatch-headless.py`, **pure extension only**:
- add `--profile <name>` to `parser()`.
- in `append_job()`: extend `pipe` with `,profile={args.profile}` when set (preserve the existing `capability=,mode=,qa=` prefix and the `f.write(f"{ts}\topen\t…")` shape).
- in `main()`, under `if args.start:` **after** the existing `check_runtime_projection(args.worktree, args.require_hook_trust)` block, when `args.profile`, gate-first then create → register → launch (same anti-leak order as claude): ① `build-home.py <name> --check` (on non-zero `return 3`, no instance created), ② `build-home.py <name> --instance <slug>` (create), ③ the existing `append_job(...)` (register before launch), ④ launch. Attach via `env={**os.environ, "CODEX_HOME": "<home-root>/<slug>.<name>"}` on the `subprocess.Popen(["sh","-c",command], …)` call — **must inherit `os.environ`** (bare dict drops `PATH` and breaks the codex exec). Do **not** set `CLAUDE_CONFIG_DIR` here (cross-harness leakage).
- **Preservation contract (Risks):** every L599-630 boundary literal must remain present verbatim — `validate_dispatch_inputs`, `--require-hook-trust`, `check_runtime_projection(args.worktree, args.require_hook_trust)`, `invalid-dispatch-{capability,mode,qa}`, `quick,light,standard,thorough,adversarial`, `Read adapters/codex/AGENTS.md first`, all `preflight.sh …` lines, `Autopilot-code execution contract`, `code-plan -> code-execute -> code-test -> code-report`, `role planning, role implementation, role verification, and role report`, `prompt_path.write_text(prompt_text, encoding="utf-8")`, `pipeline_summary.md`, `Do not claim independent QA delegation`, `Do not use adapters/claude`, `fcntl.flock`, `registry_lock={jobs}.lock`. Keep `resolve_agent_home()` and `core" / "CORE.md"` intact; do not introduce the forbidden anti-pattern (`check_codex_bin_wrappers` L542-548). `[decision: significant — editing a heavily grep-asserted file; run the codex assertion block before commit]`

### Phase 4 — liveness profile-aware (backward-compatible; parallel with Phases 2/3)

**Step 4.1** — EDIT `utilities/dispatch-liveness.sh`. Inside the `while` loop, parse the `pipe` (6th field) for `profile=<name>`. **Reset `name=""` at the top of each loop-body iteration before the case match** — otherwise a prior row that set `name` leaks into a later `profile=`-less row, misrouting it to `homes/<slug>.<prev-profile>/` (a nonexistent path → false DEAD, breaking the DP-7 backward-compat intent). Concretely:
```sh
name=""
case "$pipe" in *profile=*) name=${pipe##*profile=}; name=${name%%,*};; esac
```
Select the path on `[ -n "$name" ]`: when set (Claude-family jobs), `dir="$AGENT_HOME/.dispatch/homes/<slug>.<name>/projects/$enc"` using the same `enc` transform; otherwise keep the current `dir="$PROJ/$enc"`. `profile=` absent → unchanged path (backward-compatible). Keep `exit 3` semantics.

**Step 4.2** — MIRROR: sync byte-identical `adapters/claude/utilities/dispatch-liveness.sh`. `[pairs with 4.1]`

### Phase 5 — fleet profile exposure + liveness + mode backfill (backward-compatible; parallel with 2/3/4)

**Step 5.1** — EDIT `tools/fleet/model.py`: add `profile: Optional[str] = None` to `DispatchJob` (renders `—` when absent per the model's None convention).

**Step 5.2** — EDIT `tools/fleet/collectors/dispatch.py`:
- extend `_parse_pipe()` to also return `profile` (NEW-form `fields.get("profile")`; OLD form → `None`). Return tuple becomes `(name, mode, qa, profile)`. **All three return points must widen to 4-tuple** — NEW form (L62 `return name, fields.get("mode"), fields.get("qa"), fields.get("profile")`), the **failure path (L66 → `return None, None, None, None`)**, and OLD form (L70 `return name, m.group(2), None, None`). The failure path is the one an empty/malformed pipe actually hits (`_scan_jobs_log` calls `_parse_pipe(pipe or "")`; empty string fails the `_PIPE` regex → L66); if it stays 3-tuple the caller's 4-way unpack raises `ValueError: not enough values to unpack` and kills the entire fleet render. Update its sole caller at L351 (`_scan_jobs_log`) to unpack four (`pname, pmode, pqa, pprofile = _parse_pipe(...)`) and set `DispatchJob(..., profile=pprofile)`.
- **mode+profile backfill for proc jobs:** add a small helper `_jobs_log_fields(path)` returning `{slug: (mode, profile)}` from the latest jobs.log row per slug (reuse the last-occurrence-wins logic). In `collect()`, after building `proc_jobs`, backfill any proc job whose `mode is None` (and `profile is None`) from that map by matching `slug`. Keep this tolerant (missing file / malformed rows → empty map). *(Note (Memo 5): the **mode** backfill is not a spec §7 requirement — it is an opportunistic improvement added by this task's instructions to correct proc jobs whose argv lacks `--mode` (`mode=None`). The **profile** backfill is the spec-mandated part.)*

**Step 5.3** — EDIT `tools/fleet/collectors/dispatch.py` — **fleet liveness profile-aware (Memo 1, spec §7 (a) scan root).** This is the fleet-side counterpart of Phase 4 and closes the spec §7 `.dispatch/homes/*/` **additional scan root** requirement. Today `_job_liveness(path, now)` (L116) resolves every job's transcript under `_proj_home()/projects/<enc>` (L120), so a profile job whose transcript is isolated under `homes/<slug>.<name>/projects/` is **always misjudged DEAD** in the fleet view — the same failure Phase 4 fixes for `dispatch-liveness.sh`, unfixed on the fleet side.
- Extend `_job_liveness()` to be **profile-aware, isomorphic to the Phase 4 `dispatch-liveness.sh` logic**: widen its signature to `_job_liveness(path, now, stale_min=15, profile=None, slug=None)`. When `profile` is set (and `slug` available), compute the transcript dir as `_proj_home()/.dispatch/homes/<slug>.<profile>/projects/<enc>` (reuse the existing `_enc(path)` transform); when `profile` is None, keep the current `_proj_home()/projects/<enc>` path (backward-compatible).
- Update the sole caller in `collect()` (L378) from `_job_liveness(j.cwd, now)` to `_job_liveness(j.cwd, now, profile=j.profile, slug=j.slug)` (both fields exist on `DispatchJob` after Step 5.1 / L362).
- This makes a profile job's liveness resolve against its isolated home so it is no longer false-DEAD in fleet.

**Step 5.4** — EDIT `tools/fleet/render.py`: extend `_mq_tag()` to accept a `profile` arg and, when present, append `·<profile>` after the qa segment inside the `(…)` tag (dim `·`, profile in a dim/label color); update the width accounting `w`. Update the sole caller `_dispatch_row()` (L483) to pass `j.profile`.

**Step 5.5** — MIRROR: sync byte-identical `adapters/claude/tools/fleet/{model.py,collectors/dispatch.py,render.py}`. The `collectors/dispatch.py` mirror now also carries the **`_job_liveness()` profile-aware extension (Step 5.3)** in addition to the `_parse_pipe`/backfill edits (Step 5.2) — both live in that one file and must be present byte-identically in the adapter copy. `[pairs with 5.1-5.4]`

### Phase 6 — codex harvest home cleanup (depends on Phase 3 pipe format)

**Step 6.1** — EDIT `adapters/codex/bin/dispatch-harvest.py`, pure extension:
- **Ownership model (harness-agnostic):** this codex harvest is the single cleanup owner for **all** profile instance homes. Because claude and codex share the same `~/.claude/.dispatch/jobs.log` and `.dispatch/homes/` root (Step 2.1), harvest sees and reclaims claude profile homes (e.g. `lab-runner`) as well — no separate claude-side harvest tool is needed. Cleanup keys off the `profile=` field in the pipe, not the harness. This is what makes DP-4 hold for claude profiles.
- add `--keep-home` flag to `parser()`.
- in `main()`, when `args.mark_done and not args.keep_home`: cleanup targets must be **only rows where an actual `open` → `done` transition happened**, not the whole `matched_jobs` snapshot. `matched_jobs.append(fields.copy())` (L107) captures the pre-mutation state, and `matches()` under `--status all` also matches `running` rows — so iterating `matched_jobs` blindly would rmtree the home of a still-`running` job (e.g. `harvest --mark-done --status all --worktree X`), destroying a live session. Instead, inside the transition branch (`if args.mark_done and fields[1] == "open":`, or by collecting into a separate list within that branch) parse `profile=` from the row's `pipe` field; when present compute `home = resolve_agent_home()/.dispatch/homes/<slug>.<name>` and `shutil.rmtree(home, ignore_errors=True)` only if it exists (symlink farm → removing it never deletes the real sources). `import shutil`. (default `--status open` has matched==marked, so this only diverges for non-default selectors — but the guard must be structural, not selector-dependent.)
- **Do not touch** `matches()` / the 6-field schema (profile rides inside the pipe k=v, preserved by `"\t".join(...)`). Preserve the `fcntl.flock` and `registry_lock={jobs}.lock` literals (L627-628 asserts).

## Risks

- **Codex assertion preservation (high).** `adapters/codex/bin/dispatch-headless.py` and `dispatch-harvest.py` carry ~30 `grep -Fq` boundary literals. The edits are additive only; a dropped literal fails `check_codex_bin_wrappers`. Mitigation: run `bash tools/check-adaptation-boundary.sh` before commit; treat Phase 3/6 as extend-not-rewrite.
- **Byte-identical mirrors (high).** `build-home.py`, the three fleet files, and `dispatch-liveness.sh` all need concrete counterparts under `adapters/claude/`. For `build-home.py` byte-identity is load-bearing (marker-walk must work at both depths). Mitigation: mirror via copy, not hand-edit; the completion gates run the mirrored boundary guard too.
- **`CLAUDE_CONFIG_DIR` is an undocumented empirical behavior (DP-9).** The masked-home attach + hook firing under the instance home is verified by observation, not official docs — it can regress on a Claude release. The build-home smoke test only checks file/symlink presence, not live hook execution; live verification is a drill/oncall item, out of scope here. Flag as a standing risk.
- **Layout source ambiguity.** skills/agents live at different paths in the repo (`skills/`, `adapters/claude/agents/`) vs a runtime home (`skills/`, `agents/`). build-home resolves each source with a runtime-first / repo-fallback order; the codex `link()` skip-on-missing keeps this safe, and `--check` surfaces genuinely missing exposures.
- **Render width.** Adding `·profile` to the `(mode·qa)` tag consumes name-field width (`_NW_S`=28); long slugs truncate slightly more. Cosmetic, acceptable.
- **Fleet liveness is isomorphic to Phase 4, not redundant.** Step 5.3's `_job_liveness()` extension and Phase 4's `dispatch-liveness.sh` implement the *same* profile-aware transcript-path resolution but are **two different readers** of the same `.dispatch/homes/*/projects/` scan root (fleet collector vs. standalone liveness script) — both are required by spec §7; neither replaces the other.
- **Backward compatibility.** Phases 4/5/6 must no-op for pre-existing `profile=`-less jobs. Each parses `profile=` defensively (absent → current path/None); this includes Step 5.3's `_job_liveness()` (profile None → unchanged `_proj_home()/projects/<enc>` path).

## Verification

Run from the worktree root. All six gates must pass before commit:

1. `bash tools/check-adaptation-boundary.sh`
2. `bash adapters/claude/tools/check-adaptation-boundary.sh`
3. `bash hooks/portable-guards.test.sh`
4. `bash adapters/claude/hooks/portable-guards.test.sh`
5. `python3 tools/build-manifest.py --check`
6. **build-home smoke** (no API calls, file checks only):
   ```sh
   TMP=$(mktemp -d)
   AGENT_HOME="$PWD" python3 tools/profile/build-home.py lab-runner --instance smoke --home-root "$TMP/homes"
   test -d "$TMP/homes/smoke.lab-runner/core"          # L0 hard include
   test -e "$TMP/homes/smoke.lab-runner/CLAUDE.md"     # assembled bootstrap
   test -d "$TMP/homes/smoke.lab-runner/hooks"         # guard hooks included
   test -e "$TMP/homes/smoke.lab-runner/settings.json" # L0 hook-registration load-bearing element (harness=claude) — false-green guard
   test -d "$TMP/homes/smoke.lab-runner/skills/autopilot-lab"   # expose subset
   AGENT_HOME="$PWD" python3 tools/profile/build-home.py lab-runner --check ; echo "check exit=$?"  # expect 0
   # mirror runs identically from the adapter copy:
   AGENT_HOME="$PWD" python3 adapters/claude/tools/profile/build-home.py lab-runner --check ; echo "mirror exit=$?"  # expect 0
   rm -rf "$TMP"
   ```

Additional targeted checks:
- `python3 -c "import ast,sys; [ast.parse(open(f).read()) for f in ['tools/profile/build-home.py','adapters/claude/bin/dispatch-headless.py','tools/fleet/collectors/dispatch.py']]"` (syntax).
- Non-profile smoke (non-destruction): `python3 adapters/claude/bin/dispatch-headless.py --dry-run --worktree "$PWD" --slug t --capability autopilot-lab --mode dev --qa quick --prompt-text x` should print a dry-run with no instance created.

## Decision Points

- **Step 3.1** `[decision: significant — editing a heavily grep-asserted codex file]` — verify the full codex assertion block (`tools/check-adaptation-boundary.sh`) passes before commit.
- Autonomy otherwise routine: all other steps are additive and gated by the boundary guards.

## Scope Notes

- opencode is **out of v1 scope** (P1 — channel only fixed in spec §6/§12). No opencode wrapper/liveness/harvest edits.
- WORKFLOW/OPERATIONS §8 hybrid-routing doc updates are **out of scope** (separate cycle per spec §8).
- **`profiles/` is repo-context build input, not projected (Memo 2).** Not added to any projection surface / allowlist (see Current State). The dispatch normal flow always runs in the source-tree context (`resolve_agent_home()` → repo root via `Path(__file__).resolve()`), so build-home reads `profiles/` there. Edge note: if someone explicitly overrides `AGENT_HOME` to a *runtime* home (`~/.claude`), `profiles/` will be absent there — harmless for the normal dispatch flow (which is source-tree-context), and surfaced clearly by build-home's fail-loud on a missing declaration rather than a silent wrong result.
- **sync-skills / README dashboard wiring for `profiles/` is deferred (Memo 3).** spec §9 lists `profiles/README` as a "sync-skills auto-refresh candidate," but v1 maintains the catalog **manually** and defers the sync-skills/README dashboard integration to a separate cycle (same treatment as the §8 hybrid-routing doc). The manifest is unaffected (re-confirmed: `build-manifest.py --check` does not scan `profiles/`).
- Commits accumulate on `feat/dispatch-profiles`; **no main merge**; push to origin.

## Change History

**2026-07-02 — round 1 QA review fixes (6 issues resolved):**
- **#1 (🔴) L0 `settings.json` source path.** Corrected the Current State layout fact — `settings.json` is not at repo root; canonical is `adapters/claude/settings.json`, present at home root only as a projection. Rewrote Step 1.1 L0 hard-include as harness-aware: always `core/`+`hooks/`; harness=claude links `settings.json` via runtime-first/repo-fallback dual path; harness=codex links `hooks.json` (never claude settings — cross-harness leak guard). Added `test -e .../settings.json` to the Verification smoke test (false-green guard).
- **#2 (🟡) `_parse_pipe` returns.** Step 5.2 now requires all 3 return points widened to 4-tuple, explicitly the failure path (`return None, None, None, None`) that empty/malformed pipes hit — prevents a ValueError unpack crash killing fleet render.
- **#3 (🟡) harvest cleanup scope.** Step 6.1 now rmtree-s only rows with an actual `open`→`done` transition (inside that branch), not the `matched_jobs` snapshot — prevents deleting a running job's home under `--status all`.
- **#4 (🟡) liveness `name` leak.** Step 4.1 snippet now resets `name=""` per iteration before the case match and selects the path on `[ -n "$name" ]` — prevents a prior row's profile leaking into a `profile=`-less row (false DEAD).
- **#5 (🟡) claude instance cleanup ownership.** Step 2.1 jobs.log text rewritten from "deliberate difference" to a shared-registry model (claude+codex share `~/.claude/.dispatch/{jobs.log,homes/}`); Step 6.1 adds a harness-agnostic ownership note (codex harvest reclaims claude profile homes too). DP-4 now holds for claude profiles.
- **#6 (🟡) gate order + Popen env.** Steps 2.1/3.1 reordered to `--check` gate (return 3) → `--instance` create → `append_job` → Popen (no instance leak on gate failure), and Popen `env` must be `{**os.environ, "<VAR>": <instance>}` (inherit `os.environ` or the exec loses `PATH`).

**2026-07-02 — round 2 user-proxy (연구팀) review fixes (6 memos resolved):**
- **Memo 1 (🔴) fleet liveness profile-aware.** Added **new Step 5.3** — extend `tools/fleet/collectors/dispatch.py` `_job_liveness()` (L116) to be profile-aware (signature `_job_liveness(path, now, stale_min=15, profile=None, slug=None)`; profile set → `homes/<slug>.<profile>/projects/<enc>`), isomorphic to Phase 4; updated the `collect()` caller (L378) to pass `profile=j.profile, slug=j.slug`. Renumbered render 5.3→5.4 and mirror 5.4→5.5 (mirror now pairs 5.1-5.4 and explicitly carries the `_job_liveness` extension). Added a Risks line clarifying fleet liveness is isomorphic-not-redundant vs Phase 4 (two different readers). Closes the spec §7 (a) `.dispatch/homes/*/` scan-root gap that would false-DEAD every profile job in fleet.
- **Memo 2 (🟡) `profiles/` non-projection.** Added a Current State bullet, a Phase 0 header note, and a Scope Notes bullet: `profiles/` is a deliberate repo-context-only build input, not projected, not in the allowlist; noted the `AGENT_HOME`-override-to-runtime-home edge case is harmless for the normal source-tree dispatch flow.
- **Memo 3 (🟡) sync-skills/README deferred.** Scope Notes now states the sync-skills/README dashboard wiring for `profiles/` is deferred to a separate cycle (v1 maintains the catalog manually); manifest unaffected (re-confirmed).
- **Memo 4 (🟡) "profile" term disambiguation.** Step 0.1 README requirement adds a one-line note distinguishing dispatch **profile** (`profiles/`, `--profile`, `profile=`) from the family's **mem-profile** (`mem profile <stem>`, DB `type=profile`; `core/MEMORY.md §7.6`).
- **Memo 5 (🟢) mode-backfill provenance.** Step 5.2 backfill bullet now flags that **mode** backfill is not spec §7-mandated (opportunistic proc `mode=None` correction) while **profile** backfill is the spec-mandated part.
- **Memo 6 (🟢) finish polish.** (a) Step 0.1 anchors the concrete-model exception to `core/ADAPTATION.md` by name (not a `roles/README` derivation). (b) Steps 0.2/0.3 template guard lists now include `spec-gate` (spec-skill-gate.sh) to match the spec §5 guard set. (c) Step 1.1 states `harness: opencode` passes schema but fails loud (exit 1) at template-read in v1 (no `bootstrap-opencode.md`) — latent, must not silently degrade.
