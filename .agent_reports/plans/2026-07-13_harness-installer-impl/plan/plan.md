---
status: active
created: 2026-07-13
phases:
  - "Phase 0: manifest schema + layout decisions (foundation)"
  - "Phase 1: projector.py — INSTALL_LAYOUT recipe port (P0.1)"
  - "Phase 2: manifest.py — hash-manifest / drift / reapply (P0.3)"
  - "Phase 3: drivers/{claude,codex,opencode}.py — install()/status()/checks() (P0.4)"
  - "Phase 4: verifier.py real check lists (P0.2)"
  - "Phase 5: installer.py wiring — cmd_* real behavior (P0 integration)"
  - "Phase 6: mem import + ~/.local/bin launcher symlinks (P0.5)"
  - "Phase 7: P1 — plugin channel wrapping + Claude plugin content (boundary marked)"
---

# harness-installer — Implementation Cycle 1

## Goal

Fill `tools/install/` from scaffold stubs into a working installer: symlink projection (INSTALL_LAYOUT mechanization), read-only `verify` check lists, hash-manifest with deterministic `git merge-file` reapply, three runtime drivers that call existing adapter scripts (no reimplementation), plus `mem import` and PATH launcher install. All demonstrated under a throwaway temp `HOME` + `--dry-run` — never touching real runtime homes.

## Current State Analysis

### Repo layout reality (verified this worktree, branch `harness-installer-impl`)
- Canonical Claude surfaces live at **repo root**: `core/`, `capabilities/`, `roles/`, `commands/`, `skills/`, `agents/`, `hooks/`, `utilities/`, `scaffolds/`, `tools/`, `loops/`, `manifest.json`. Claude is the **native** runtime.
- Adapter surfaces: `adapters/claude/`, `adapters/codex/`, `adapters/opencode/`. Claude runtime-owned files: `adapters/claude/{CLAUDE.md,settings.json,statusline.sh,keybindings.json?}`.
- **`{claude,codex,opencode}_setting/` projection directories EXIST and are git-tracked in this worktree** (symlink-farm projection dirs; e.g. `claude_setting/{CLAUDE.md,agents,agent-modes,bin,...}`, `codex_setting/bin/preflight.sh`, `opencode_setting/...`). `INSTALL_LAYOUT.md`'s symlink recipe references them as sources (`$AGENT_HOME/claude_setting/$p`, `$AGENT_HOME/codex_setting/...`, `$AGENT_HOME/opencode_setting/...`) and those sources resolve correctly with `AGENT_HOME=<repo root>`. (Note: these are symlinked dirs — a plain glob may not traverse them; `Read`/`ls` through the symlink does.) The projector resolves source paths against `AGENT_HOME`; presence is the **default expectation**, with a defensive "skip if absent" only as a safety net (not the normal path).

### Reusable scripts (call, never reimplement — verified present)
- `adapters/codex/bin/sync-native-{skills,agents,modes,plugin}.py` — argparse, `--check` = read-only projection verify; bare call = (re)generate. (verified `--check` flag present.)
- `adapters/opencode/bin/sync-native-{skills,agents,commands}.py` — same `--check` interface (verified in `sync-native-skills.py:121`).
- **Claude has NO `sync-native-*.py`** (native runtime — root dirs ARE the SoT). Claude projection = pure symlinks + copy-once, no generator.
- `adapters/codex/bin/preflight.sh` + `adapters/opencode/bin/preflight.sh` — subcommand contracts (`capability-info`, `role`, `permissions`, `mcp`, `headless`, `status`, `mode-info`, `dispatch`, `harvest`, `liveness`, ... verified line 378+). **Claude has NO `preflight.sh`** (no `*_setting/bin/preflight.sh` anywhere).
- `adapters/claude/bin/install-windows.sh` — idempotent Windows repair (HOME env injection into settings.json + symlink→copy). Call it; do not reimplement (`set -euo pipefail`, exits 66/69 on missing canonical/python).
- `tools/build-manifest.py --check` — projection drift generator (used in Migration Order).
- `tools/memory/mem.py` — `mem import <path>` restores `dump.jsonl` → `memory.db` (subparser `import`, `mem.py:3562/3654`; `import_dump()` at 1757 DELETEs then replays for exact restore). STORE = `$AGENT_HOME/memory` or `$MEM_STORE` (`mem.py:30-32`); `dump.jsonl` lives in the separate `agent-memory` repo, not `agent_setting`.
- `tools/fleet/fleet.sh` — launcher precedent for the `~/.local/bin` symlink pattern (INSTALL_LAYOUT lines 94-98).
- Plugin marketplaces: `adapters/codex/plugin-marketplace/.agents/plugins/marketplace.json` (working, reuse); `adapters/claude/plugin-marketplace/` skeleton (`marketplace.json` + `plugins/agent-harness-claude/.claude-plugin/plugin.json`, content incomplete).

### Scaffold source state (commit 9792fd3)
- `tools/install/harness.sh` — POSIX launcher, complete. **Do not touch.**
- `installer.py` — argparse tree + exit-code constants (`EXIT_OK=0/FAIL=1/VERIFY_FAIL=2/BLOCKED=3/DRIFT=4/USAGE=64`) + `--json` shape complete. `cmd_install` (101) calls `projector.plan()` but only reports plan counts (TODO: real `driver.install()` + `manifest.record()`). `cmd_verify` (115) already wires `verifier.run(rt, driver)` — works once drivers return checks. `cmd_update` (130) calls `manifest.check_drift()` (currently `[]`). `cmd_status` (139) stubs "channel=미확인". `cmd_uninstall` (151) stub. `resolve_runtimes()` (82) + `emit()` (92) complete.
- `projector.py` — `plan(runtimes, scope)` returns `{rt: []}` always (`_PROJECTION_STUB` empty).
- `manifest.py` — `record()`/`reapply()` raise `NotImplementedError` (gate now passed); `check_drift()` returns `[]`.
- `verifier.py` — `run(runtime, driver)` executes `driver.checks()`; falls back to a single "no-checks" placeholder when empty.
- `drivers/{claude,codex,opencode}.py` — `install()`/`status()` raise `NotImplementedError`; `checks()` returns `[]`. Each module exports `RUNTIME` constant. `drivers/__init__` exposes `get_driver()` + `RUNTIMES` (imported by installer).

## Change Plan

Phase ordering (hard dependencies): **Phase 0 → 2 → 5** (manifest schema must exist before manifest impl before installer wiring). **Phase 1 → 3 → 4** (projector before drivers before verifier check lists). Phase 5 depends on 1+2+3. Phase 6 independent (can parallelize with 1-4). Phase 7 is P1.

---

### Phase 0 — Foundation: manifest schema + layout constants (do first)

**Step 0.1 — Add `tools/install/paths.py` (new module): central path resolution.**
- Add `agent_home()` → resolves repo root: env `AGENT_HOME` if set, else walk up from `__file__` to git root. Returns `pathlib.Path`.
- Add `runtime_home(runtime, scope)` → target dir per runtime:
  - claude → `$HOME/.claude`
  - codex → `$HOME/.codex`
  - opencode global → `$HOME/.config/opencode`; opencode project → `$PWD/.opencode` (scope=project). Also `opencode_data = $HOME/.local/share/opencode` (runtime-owned, never written).
- Add `harness_state_dir(runtime, scope)` → `runtime_home / ".harness"` (installer-owned subtree inside runtime home: manifest + pristine + backups live here so uninstall is self-contained and travels with the target).
- Add `resolve_source(relpath)` → `agent_home() / relpath`, plus `source_exists()` helper (used by projector SKIP logic).
- **Done when**: `python3 -c "import paths; print(paths.agent_home())"` (from `tools/install/`) prints the repo root, and `paths.runtime_home('claude','global')` prints `<temp HOME>/.claude` under a temp `HOME`.

**Step 0.2 — Decide + document manifest JSON schema (write as module docstring in `manifest.py`, no logic yet).**
- Manifest file: `<runtime_home>/.harness/manifest.json`:
  ```json
  {"schema": 1, "runtime": "claude", "scope": "global",
   "version": "<repo git SHA at install>", "timestamp": "<iso8601>",
   "files": {"settings.json": "<sha256hex>", "keybindings.json": "<sha256hex>"}}
  ```
- Pristine snapshots: `<runtime_home>/.harness/pristine/<relpath>` — the **repo-canonical bytes copied at install time** (3-way merge base). Immutable until next successful install refreshes them (guard: never overwrite pristine with a newer-release copy while drift is unresolved — impl-inputs §A trap #3407).
- Backups (unified single dir, impl-inputs §A adoption note): `<runtime_home>/.harness/local-patches/<relpath>` — full-file copy of a user-modified file, taken pre-wipe.
- `backup-meta.json`: `{"from_version": "<sha>", "pristine_hashes": {"<relpath>": "<sha256>"}}` alongside backups.
- **Manifest scope for cycle 1 = copy-once files only**: Claude `settings.json`, `keybindings.json` (+ Windows copies made by install-windows.sh). Symlinks excluded (self-canonical). OpenCode `opencode.json` is **merge-managed, tracked separately** (not a pure copy) — cycle 1 records only its harness-managed fragment presence, deferring full merge-manifest to a later cycle (mark in Risks).
- Shared-with-HLS note: schema key names chosen to match `tools/build-manifest.py` conventions where they overlap; do not fork the hash algorithm (SHA-256 hex, same as GSD/HLS).
- **Done when**: `manifest.py` docstring documents the exact schema + directory layout; no behavior change yet (functions still raise/return stub).

---

### Phase 1 — projector.py: port the INSTALL_LAYOUT symlink recipe (P0.1)

**Target file**: `tools/install/projector.py`. Replace `_PROJECTION_STUB` + `plan()`.

**Step 1.1 — Encode per-runtime projection tables as data (mirror INSTALL_LAYOUT exactly).**
Represent each entry as a dict with an explicit `action` type so runtime-owned copies are separated from symlinks:
- `{"action": "symlink", "source": "<relpath under AGENT_HOME>", "dest": "<abs under runtime_home>"}`
- `{"action": "copy_once", "source": ..., "dest": ...}` (settings.json, keybindings.json — never re-link, INSTALL_LAYOUT lines 29-35)
- `{"action": "symlink_glob", "source_dir": ..., "dest_dir": ..., "pattern": "*.toml" | "*" | "*/*.md"}` (per-file fan-out loops)
- `{"action": "delegate", "cmd": ["bash", "adapters/claude/bin/install-windows.sh"]}` (Windows branch — do not reimplement)
- `{"action": "merge", ...}` (opencode.json non-destructive merge — handled by opencode driver, projector only emits the intent)

Tables to encode (source = INSTALL_LAYOUT.md):
- **claude** (lines 21-35): symlink each of `CLAUDE.md README.md core commands skills agents agent-modes hooks utilities tools scaffolds loops manifest.json statusline.sh track-toggle.sh` from `claude_setting/<p>` → `~/.claude/<p>`; `copy_once` for `settings.json keybindings.json`. (`claude_setting/` exists and is git-tracked; sources resolve against `AGENT_HOME` — presence is the default, skip-if-absent is only a safety net.)
- **codex** (lines 110-138): fixed symlinks (`agent-harness`, `AGENTS.md`, `agent-core`, `agent-capabilities`, `agent-roles`, `agent-bin`, `agent-tools`, `agent-utilities`, `agent-scaffolds`, `agent-skills`, `agent-modes`, `agent-agents`, `agent-plugin-marketplace`, `agent-hooks`, `agent-config`, `hooks.json`) + two `symlink_glob` fan-outs (`codex-skills/*` → `.codex/skills/`, `codex-agents/*.toml` → `.codex/agents/`). scope=project rewires the agents glob into `<project>/.codex/agents/`.
- **opencode** (lines 177-225): pointer symlink + adapter-owned surface symlinks + agent/command per-file glob fan-outs + `opencode.json` merge intent + plugins symlink. **Use the local 1.17.13 singular wiring** (`agent/`, `command/`, `skills.paths`) per impl-inputs §B — do NOT switch to plural; INST-OPEN-4 stays OPEN.

**Step 1.2 — `plan(runtimes, scope="global")` computes the resolved plan.**
- For each runtime, expand tables via `paths.resolve_source()` + `paths.runtime_home()`. Expand `symlink_glob` by listing `source_dir` (if it exists) into concrete per-file entries.
- Annotate each entry with `"source_present": bool`. In the normal case sources are present (they exist in this worktree); a source that is genuinely missing becomes `{"action": "skip", "reason": "source absent: <path>", ...}` (parity-loss SKIP pattern, PRD "parity-loss warning") — this is a defensive safety net, not the expected path.
- Return shape stays `{runtime: [entry, ...]}` (installer already consumes `plan.get(rt, [])`).
- **Done when**: with temp `HOME` + `AGENT_HOME=<repo root of this worktree>`, `harness install --dry-run --json` shows the **full resolved symlink/copy_once list** per runtime (real `claude_setting/`→`~/.claude/`, `codex_setting/`→`~/.codex/`, `opencode_setting/`→`~/.config/opencode/` entries), with **no `skip: source absent`** entries. End-to-end is verifiable in THIS worktree — no separate materialized checkout needed.

---

### Phase 2 — manifest.py: hash-manifest / drift / reapply (P0.3) [depends on Phase 0]

**Target file**: `tools/install/manifest.py`. Implement the three functions + helpers. **All deterministic code — no LLM merge** (impl-inputs §A adoption).

**Step 2.1 — Helpers.**
- `_sha256(path)` → hex digest (streamed).
- `_manifest_path(runtime, scope)`, `_pristine_path(...)`, `_backup_path(...)` via `paths.harness_state_dir`.
- `_safe_relpath(rel)` → reject absolute, `..`, NUL, symlink-escape (impl-inputs §A #7 path-safety); used on every manifest-derived relpath before touching disk.
- `_load_manifest`/`_write_manifest` (JSON, sorted keys, atomic write via temp+rename).

**Step 2.2 — `record(runtime, files, scope="global", version=None)`** (replaces `NotImplementedError`).
- `files` = list of copy-once entries `{relpath, source_abs, dest_abs}` from the projector's `copy_once` actions.
- For each: ensure pristine snapshot exists (copy `source_abs` → pristine/<relpath> **only if absent or an install is refreshing after clean reapply** — never clobber pristine while drift unresolved), compute SHA-256 of the **installed dest bytes**, add to `files` map.
- Write manifest with `version` = current repo git SHA (`git rev-parse HEAD`, fallback "unknown").
- Idempotent: re-`record` overwrites manifest but preserves existing pristine.
- **Done when**: after a temp-HOME install, `<temp>/.claude/.harness/manifest.json` lists `settings.json`/`keybindings.json` with hashes and `<temp>/.claude/.harness/pristine/settings.json` exists.

**Step 2.3 — `check_drift(runtimes, scope="global")`** (replaces `return []`).
- For each runtime with a manifest: recompute SHA-256 of each dest file, compare to recorded hash. Mismatch = user-modified → append `{"runtime", "path", "detail": "hash mismatch"}`. Missing dest = `{"detail": "manifest file absent"}`.
- **Invariant** (impl-inputs §A trap): hash mismatch ALWAYS means user content present — never treat "looks mechanical" as skip.
- **Done when**: install into temp HOME, hand-edit `<temp>/.claude/settings.json`, `harness update --json` reports that path in `drift[]` and exits `EXIT_DRIFT` (4).

**Step 2.4 — `reapply(runtimes, scope="global")`** (replaces `NotImplementedError`).
- Pre-wipe pass (order invariant from GSD `saveLocalPatches`-before-wipe): for each drifted file, copy current dest → `local-patches/<relpath>` (full copy) and record `backup-meta.json` with `from_version` + `pristine_hashes`.
- 3-way merge via **`git merge-file`**: `git merge-file -p --diff3 <ours=current-dest> <base=pristine> <theirs=new-canonical-source>` → merged bytes. (pristine = old-release base; theirs = current repo source.)
- Write merged result to dest **only if no conflict markers**; on conflict, leave conflict-marked file + report `{"path", "status": "conflict"}` and DO NOT force-merge (PRD "3-way 충돌은 명시 report").
- **Deterministic post-merge verifier** (impl-inputs §A #5): assert every meaningful (non-blank, non-marker) line of `local-patches/<relpath>` is a substring of the merged output; if not, mark `verify_failed` and keep backup. No LLM.
- After successful reapply, refresh pristine to the new-canonical bytes + rewrite manifest hashes.
- Return `{"reapplied": [...], "conflicts": [...], "verify_failed": [...]}`.
- **Done when**: install → edit dest → change the repo-canonical source → `harness update --reapply --json` merges cleanly (or reports a conflict) and the merged file contains the user's edit lines; `local-patches/` holds the backup.

---

### Phase 3 — drivers/{claude,codex,opencode}.py: install()/status()/checks() (P0.4) [depends on Phase 1]

Each driver's `install()` applies the projector plan (symlink/copy_once/glob/delegate/merge), calls the right generators, and records the manifest. **checks() returns a list of zero-arg callables**, each returning `{"id","ok","detail"}` (verifier.run already iterates them).

**Step 3.1 — `drivers/claude.py`.**
- `install(scope, plugin, dry_run)`: apply claude projector plan. Claude has no generator — pure symlink + `copy_once`. On `copy_once`, call `manifest.record()` for `settings.json`/`keybindings.json`. If host is Windows (detect `os.name == 'nt'` or MSYS/`sys.platform`), run the `delegate` entry (`adapters/claude/bin/install-windows.sh`) instead of raw symlinks. `dry_run=True` → return planned actions without touching disk. `plugin=True` → Phase 7 wrapping (cycle-1: emit `SKIP(claude): plugin channel — P1, see Phase 7` unless P1 landed).
- `status()`: read manifest (version SHA, file count), run `check_drift(["claude"])`, return `{channel, version, drift_count}`.
- `checks()`: list of read-only callables (implemented as check bodies in Phase 4).

**Step 3.2 — `drivers/codex.py`.**
- `install()`: apply codex projector plan (fixed symlinks + agents/skills globs). **Always keep symlink projection even when `plugin=True`** — agents `.toml`/prompts/config fragment are not plugin-carriable (INST-D-5; scaffold docstring already warns). No copy-once files for codex → manifest.record called with empty copy set (or skipped). Optionally run `sync-native-{skills,agents,modes,plugin}.py` (bare, to regenerate projections) — gate behind a `--generate` intent; default install assumes projections already generated, verify catches drift.
- `status()`: channel detection — check `~/.codex/agent-harness` pointer + plugin marketplace presence.
- `checks()`: Phase 4.

**Step 3.3 — `drivers/opencode.py`.**
- `install()`: apply opencode projector plan; `opencode.json` **non-destructive merge** — load existing user config, add `instructions[]` / `skills.paths` / `plugin[]` entries **only if absent**; on same-key-different-value conflict → **report + stop** (`EXIT_BLOCKED` path), no auto-resolution (PRD "의미↔규칙 경계 체크"). Use local 1.17.13 singular wiring (impl-inputs §B).
- `status()`: pointer + config-merge presence.
- `checks()`: Phase 4.
- **Done when (all three)**: `harness install <rt> --dry-run --json` returns a non-empty `checks[]`/plan and no `NotImplementedError`; `status` returns a real channel/version dict.

---

### Phase 4 — verifier.py real check lists (P0.2) [depends on Phase 3]

**Target**: implement the callables returned by each driver's `checks()`. `verifier.run()` needs no change (already iterates). All checks **read-only** (safety constraint). Mechanize Migration Order (INSTALL_LAYOUT lines 239-512).

**⚠️ Per-runtime asymmetry (do NOT apply a uniform check set across all three):** Claude is the **native** runtime — there are **no `adapters/claude/bin/sync-native-*.py` generators** and **no `claude_setting/bin/preflight.sh`**. So the "sync-native `--check`" and "preflight contract smoke" checks apply to **codex and opencode only**. The Claude verify path instead relies on projection-symlink existence + `tools/build-manifest.py --check` + compile smoke + (CLI-gated) bootstrap load. Check counts are intentionally uneven: claude ≈ 3-4 checks (no sync-native, no preflight), codex ≈ 4 sync-native `--check` + preflight + symlink + bootstrap, opencode ≈ 3 sync-native `--check` + preflight + symlink + drift-watch + bootstrap.

**Step 4.1 — Shared check helpers** (put in `verifier.py` or a `checks_common.py`): `check_symlink(dest, expected_source)` (exists + resolves to expected), `check_cmd(argv, must_match=[regex])` (run subprocess read-only, grep stdout), `check_file_exists(path)`.

**Step 4.2 — claude checks** (no preflight.sh; native runtime):
- (a) projection symlink existence for each claude projector entry (dest is a symlink → expected source).
- (b) `python3 tools/build-manifest.py --check` exit 0 (projection drift generator).
- (c) compile smoke: `python3 -c "compile(...)" tools/build-manifest.py tools/memory/mem.py` (Migration Order line 252).
- (d) bootstrap load smoke (optional, only if `claude` CLI present): temp CODEX-analog — `claude` has no equivalent `debug prompt-input` guaranteed; gate behind CLI presence, else `SKIP(claude): bootstrap smoke — claude CLI absent`.

**Step 4.3 — codex checks** (from Migration Order lines 255-402):
- (a) projection symlink existence (codex projector entries).
- (b) `adapters/codex/bin/sync-native-{skills,agents,modes,plugin}.py --check` each exit 0.
- (c) preflight contract smoke — 1-2 subcommands: `adapters/codex/bin/preflight.sh capability-info autopilot-code` must emit `native_skill_path=...`; `preflight.sh role fast reviewer` must emit `adapter=codex`. (Keep to 1-2 per safety/scope; full 260-line battery is not cycle-1.)
- (d) bootstrap load smoke (only if `codex` CLI present): temp CODEX_HOME symlink `codex_setting/AGENTS.md`, `codex debug prompt-input 'bootstrap check'` greps `AGENTS.md — Codex Adapter Bootstrap`. Gate behind CLI presence else SKIP.

**Step 4.4 — opencode checks** (from Migration Order lines 403-511):
- (a) projection symlink existence (opencode projector entries, singular wiring).
- (b) `adapters/opencode/bin/sync-native-{skills,agents,commands}.py --check` each exit 0.
- (c) preflight contract smoke — `adapters/opencode/bin/preflight.sh capability-info autopilot-code` emits `native_skill_path=...`; `preflight.sh role fast reviewer` emits `adapter=opencode`.
- (d) **doc-vs-wiring drift watch** (impl-inputs §B mandate): a check that records local opencode version + whether plural dirs (`skills/`,`agents/`,`commands/`) exist; passes (ok=True) under singular 1.17.13 but emits `detail` naming the drift so a future version bump surfaces it. This is the single INST-OPEN-4 sentinel.
- (e) bootstrap load smoke (only if `opencode` CLI present): temp HOME + `OPENCODE_CONFIG_CONTENT` per Migration Order 486-493, grep `opencode_setting/AGENTS.md`. Gate behind CLI presence else SKIP.
- **Done when**: `harness verify --json` returns a `checks[]` with real ids (`claude.symlink.core`, `codex.sync-skills`, `opencode.drift-watch`, ...) and exit 0/2 driven by actual results, not the "no-checks" placeholder.

---

### Phase 5 — installer.py wiring: cmd_* real behavior (P0 integration) [depends on 1,2,3]

**Target**: `tools/install/installer.py` cmd_* functions.

**Step 5.1 — `cmd_install`**: replace the TODO loop (line 108-110). For each runtime call `driver.install(scope=args.scope, plugin=args.plugin, dry_run=args.dry_run)`; collect returned action reports into `checks[]`; surface `SKIP(...)` lines for absent sources / unsupported surfaces (parity-loss). On BLOCKED conditions (active runtime process, opencode merge conflict) return `EXIT_BLOCKED`. Keep `--json` shape (`{runtime, channel, checks, drift, exit, lines}`).
**Step 5.2 — `cmd_status`**: replace stub (line 145-147) with `driver.status()` results (channel/version/drift).
**Step 5.3 — `cmd_update`**: **remove the `if args.reapply` drift gate** at `installer.py:132` (`drift = manifest.check_drift(runtimes) if args.reapply else []`) so **plain `update` always computes + reports drift** (drift detection must not require `--reapply`). New behavior: always `drift = manifest.check_drift(runtimes)`; if drift present and **not** `--reapply` → `EXIT_DRIFT` (4) with the drift list (user must decide). When `--reapply` → call `manifest.reapply()` and report `reapplied/conflicts/verify_failed`; map conflicts → `EXIT_DRIFT` (or BLOCKED), clean → `EXIT_OK`.
**Step 5.4 — `cmd_uninstall`**: implement manifest-scoped removal — read manifest, remove only enumerated files + symlinks the projector created, rmdir empty shared dirs only, delete `.harness/manifest.json` last. Never touch runtime credentials/sessions/projects (ownership boundary). Back up before removing (reuse local-patches). Dry-run lists what would be removed.
- **Done when**: full temp-HOME loop (install → status → update → uninstall) runs with correct exit codes and `--json` shapes; uninstall leaves temp HOME with only non-manifest files.

---

### Phase 6 — mem import + ~/.local/bin launcher symlinks (P0.5) [independent, parallelizable]

**Step 6.1 — memory restore in `cmd_install` (or a `drivers`-neutral helper `bootstrap.py`).**
- After Claude install, if `$MEM_STORE/memory.db` (default `$AGENT_HOME/memory/memory.db`) is missing but `dump.jsonl` exists, call `python3 tools/memory/mem.py import <dump.jsonl>` (reuse — do not reimplement). Guard: only when DB absent (idempotent). Under temp HOME, honor `MEM_STORE` override so tests don't touch the real memory repo.
- **Done when**: with `MEM_STORE=<temp>/mem` + a small `dump.jsonl`, install creates `<temp>/mem/memory.db`; re-run is a no-op.

**Step 6.2 — PATH launcher symlinks.**
- Install `~/.local/bin/harness` → `tools/install/harness.sh` and `~/.local/bin/fleet` → `tools/fleet/fleet.sh` (INSTALL_LAYOUT lines 94-98 pattern). `mkdir -p ~/.local/bin`; `ln -sfn`. **PATH-collision guard** (INST-OPEN-2): if an existing `harness` on PATH is not our symlink, warn + SKIP (don't clobber). Dry-run prints intended links.
- **Done when**: under temp HOME, install creates `<temp>/.local/bin/{harness,fleet}` symlinks; an existing foreign `harness` triggers a warn+skip line.

---

### Phase 7 — P1: plugin channel wrapping + Claude plugin content (BOUNDARY)

**Cycle-1 boundary decision:**
- **IN this cycle (if capacity remains)**: `install --plugin` CLI wrapping for **Codex** (reuse working `adapters/codex/plugin-marketplace/`): `codex plugin marketplace add <path>` + `codex plugin add agent-harness-codex@agent-harness`, plus a verify item. This is low-risk (marketplace already works, Migration Order 353-357 proves the commands). **Step 7.1.**
- **DEFERRED to next cycle (explicitly)**: 
  - **Claude plugin content generator** — physically materializing `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/` (skills/agents/hooks/.mcp.json/bin) from SoT via a new sync-native generator. This is large (new generator + self-contained build-time inclusion, PRD "설치본은 self-contained") and belongs to its own cycle. Cycle-1 leaves the skeleton + emits `SKIP(claude): plugin channel — deferred to next cycle`.
  - **Claude `install --plugin` wrapping** (`claude plugin marketplace add` + `claude plugin install`) — depends on the content generator above; deferred with it.
- **Step 7.1 (Codex plugin wrap, P1-in-cycle if time)**: in `drivers/codex.py`, `plugin=True` path calls the two `codex plugin ...` commands (subprocess, `--json`), gated behind `codex` CLI presence (else SKIP). Add a codex verify check that the plugin marketplace resolves. Symlink projection still runs (INST-D-5).
- **Done when**: `harness install codex --plugin --dry-run` prints the planned `codex plugin marketplace add`/`plugin add` commands; Claude `--plugin` prints the deferral SKIP.

## Risks

- **Symlink/copy on real homes**: every disk-mutating action must be guarded by `dry_run` in demos and pointed at a temp `HOME`. The drivers must never write to `~/.claude`/`~/.codex`/`~/.config/opencode` during testing (see Verification).
- **install-windows.sh delegation**: only fires on Windows; on Linux the `delegate` action is a no-op. Ensure platform detection doesn't accidentally run it under WSL if POSIX symlinks work there (WSL should take the Linux symlink path).
- **pristine clobber** (impl-inputs §A #3407): refreshing pristine with new-release bytes while drift is unresolved inverts the 3-way delta. Guard: pristine only refreshed after a *successful, verified* reapply, never mid-drift.
- **`git merge-file` availability**: reapply needs `git` on PATH. Gate with a preflight check; if absent, degrade to "backup + report, no auto-merge" (never silent).
- **opencode.json merge**: same-key/different-value must stop+report, not guess (only semantic-boundary candidate, resolved as a rule per PRD).
- **Signature/caller impact**: `projector.plan()` return shape changes from `{rt: [ {source,dest} ]}` to `{rt: [ {action, ...} ]}`. Only caller is `installer.cmd_install` (line 104/110) which currently reads `len(plan.get(rt, []))` — still valid. Driver `install()` signatures `(scope, plugin, dry_run)` already match the scaffold; no caller change needed. `manifest.record/check_drift/reapply` signatures preserved (installer already calls `check_drift(runtimes)`; add optional `scope` with default). `verifier.run(runtime, driver)` unchanged.

### Unresolved

- **Claude native-runtime asymmetry (design constraint, not a blocker)**: `INSTALL_LAYOUT.md`'s projection sources under `$AGENT_HOME/{claude,codex,opencode}_setting/` **all exist and are git-tracked in this worktree** and resolve with `AGENT_HOME=<repo root>`; end-to-end is verifiable here with no separate checkout. The one asymmetry to keep in mind (handled in Phase 4): Claude is native, so there is **no `claude_setting/bin/preflight.sh` and no `adapters/claude/bin/sync-native-*.py`** — only codex/opencode have those. Verifier check sets are therefore intentionally uneven per runtime (Phase 4 note). The projector still resolves sources against `AGENT_HOME` (never hardcoded absolute paths) so an HLS canonical restructure flows through without edits.
- **INST-OPEN-4 (still OPEN per PRD)**: OpenCode plural-dir / `skills.paths` migration deferred; cycle-1 keeps singular 1.17.13 wiring and adds only the drift-watch sentinel (Phase 4.4d).
- **OpenCode opencode.json merge-manifest (AMBIGUOUS)**: PRD says hash-manifest tracks *copied* files only; `opencode.json` is merge-managed, not copied. Cycle-1 records only fragment-presence, deferring a full merge-aware manifest. Confirm with spec owner whether merge-managed files need drift tracking too.

## Verification

All commands run from repo root with a **throwaway HOME** and **AGENT_HOME/MEM_STORE overrides** — never the real runtime homes. Baseline setup block (prepend to each phase check):

```bash
cd /home/Uihyeop/agent_setting-wt/harness-installer-impl
export REAL_REPO="$PWD"
export HOME="$(mktemp -d)"                 # throwaway target home — isolates ~/.claude etc.
export AGENT_HOME="$REAL_REPO"             # source repo (see INST-STALE-1 re: *_setting/)
export MEM_STORE="$HOME/mem"; mkdir -p "$MEM_STORE"
# harness.sh is a POSIX sh launcher that exec's `python3 installer.py "$@"` — invoke it via sh, not python.
harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }
# (equivalent direct form if a shell function is inconvenient:
#   python3 "$REAL_REPO/tools/install/installer.py" <args> )
```

**Phase 0 (paths/schema):**
```bash
python3 -c "import sys; sys.path.insert(0,'$REAL_REPO/tools/install'); import paths; \
  print(paths.agent_home()); print(paths.runtime_home('claude','global'))"
# expect: repo root; then $HOME/.claude   (under temp HOME)
```

**Phase 1 (projector dry-run):**
```bash
harness install --dry-run --json | python3 -m json.tool
# expect: per-runtime plan with action-typed entries. In THIS worktree (no *_setting/):
#   entries with "action":"skip","reason":"source absent: .../claude_setting/core" etc.
# When AGENT_HOME points at a materialized checkout: full symlink+copy_once list, no skips.
```

**Phase 2 (manifest record + drift + reapply):**
```bash
# record: copy_once sources (claude_setting/settings.json, keybindings.json) exist in this worktree.
mkdir -p "$HOME/.claude"
harness install claude --json                               # real writes into $HOME/.claude only
test -f "$HOME/.claude/.harness/manifest.json" && echo "manifest OK"
# drift: hand-edit a recorded copy-once file, then:
echo '// user edit' >> "$HOME/.claude/settings.json" 2>/dev/null || true
harness update --json; echo "exit=$?"          # expect drift[] non-empty, exit=4
# reapply: change canonical source, then:
harness update --reapply --json                # expect reapplied[] and merged file keeps '// user edit'
grep -q 'user edit' "$HOME/.claude/settings.json" && echo "reapply preserved edit"
```

**Phase 3-4 (drivers + verify, read-only):**
```bash
harness verify --json | python3 -m json.tool
# expect: checks[] with real ids (claude.symlink.*, codex.sync-skills, opencode.drift-watch, ...),
#   exit 0 if all pass else 2. NO disk mutation (all checks read-only).
harness verify codex --json     # subset
harness status --json           # channel/version/drift per runtime, no NotImplementedError
```

**Phase 5 (full lifecycle, temp HOME):**
```bash
harness install all --dry-run --json     # plan only, no writes
harness install claude --json            # real writes into $HOME/.claude only
harness status --json
harness update --json
harness uninstall claude --dry-run --json  # lists manifest-scoped removals
harness uninstall claude --json            # removes only manifest entries + created symlinks
test ! -f "$HOME/.claude/.harness/manifest.json" && echo "clean uninstall"
# assert real homes untouched:
test -z "$(ls -A ~/.claude 2>/dev/null | grep -v '^$')" || true   # temp HOME only
```

**Phase 6 (mem import + launchers):**
```bash
printf '{"id":"t1","type":"note","body":"probe","tags":[],"links":[]}\n' > "$MEM_STORE/dump.jsonl"
harness install claude --json >/dev/null 2>&1 || true
test -f "$MEM_STORE/memory.db" && echo "mem import OK"     # DB created from dump
test -L "$HOME/.local/bin/harness" && test -L "$HOME/.local/bin/fleet" && echo "launchers OK"
# collision guard:
printf '#!/bin/sh\n' > "$HOME/.local/bin/harness2"; # foreign name test as needed
```

**Phase 7 (plugin dry-run):**
```bash
harness install codex --plugin --dry-run --json
# expect planned: codex plugin marketplace add <path> + codex plugin add agent-harness-codex@agent-harness
harness install claude --plugin --dry-run --json
# expect: SKIP(claude): plugin channel — deferred to next cycle
```

**Safety assertion (run last, must hold throughout):** no command above writes outside `$HOME` (temp) or `$MEM_STORE` (temp). The real `~/.claude`/`~/.codex`/`~/.config/opencode` are never in scope because `HOME` is reassigned to a mktemp dir before any `harness` call. `code-test` must confirm this by checking the real homes' mtimes are unchanged after the run.

## Change History

- **2026-07-13 (plan-check correction pass)** — fixed 2 BLOCKING + 1 non-blocking issue found by standard-tier plan-check (filesystem-verified against the worktree):
  - **B1**: Corrected an inverted premise. `{claude,codex,opencode}_setting/` projection-source dirs **DO exist and are git-tracked** (my earlier glob failed to traverse the symlinked dirs; `Read` through them confirms presence). Rewrote Current State layout bullet, Phase 1.1 claude note, Phase 1.2 done-when (now expects a full resolved symlink plan with **no** `skip: source absent`), Phase 2 verification comment, and replaced the Unresolved "INST-STALE-1 (CLEAR-BUT-STALE, dirs absent)" entry with a "Claude native-runtime asymmetry" design-constraint note. Preserved the verified nuance: Claude is native → no `claude_setting/bin/preflight.sh`, no `adapters/claude/bin/sync-native-*.py`; added an explicit per-runtime asymmetry banner to Phase 4 so check sets are not applied uniformly (claude ≈3-4 checks vs codex/opencode which add sync-native `--check` + preflight).
  - **B2**: Fixed the non-runnable Verification baseline. `tools/install/harness.sh` is a POSIX **sh** launcher (exec's `python3 installer.py "$@"`), not python — replaced `alias harness="python3 .../harness.sh"` with a shell function `harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }` (+ direct `python3 installer.py` fallback note).
  - **N1**: Made `cmd_update` internally consistent — Phase 5.3 now plans **removal of the `if args.reapply` drift gate** at `installer.py:132`, so plain `update` always computes+reports drift (matching Phase 2.3's `harness update --json` → drift[]/exit 4 expectation).
