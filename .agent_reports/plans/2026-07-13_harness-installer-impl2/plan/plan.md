---
status: draft
created: 2026-07-13
cycle: 2
carryover_from: .agent_reports/plans/2026-07-13_harness-installer-impl/
spec: .agent_reports/spec/harness-installer/prd.md
prd_open_touched: "INST-OPEN-1 (file-level hook adopt/exclude decided here) + INST-OPEN-3 (INSTALL_LAYOUT reduction). This stage does NOT edit prd.md — code-report records whether/how the PRD OPEN section should be updated by the main orchestrator's autopilot-spec update."
phases:
  - "Phase 1: adapters/claude/bin/sync-native-plugin.py — Claude plugin content generator + --check (P0)"
  - "Phase 2: drivers/claude.py — install --plugin wrapping (claude plugin marketplace add + plugin install) (P0)"
  - "Phase 3: drivers/claude.py checks() + verifier — plugin marketplace/install/generator-drift verify checks (P0)"
  - "Phase 4: INSTALL_LAYOUT.md reduction — manual recipe → contract + harness install/verify reference (INST-OPEN-3, P1)"
  - "Phase 5: code-test — isolation contract (temp HOME single self-contained script, real-home determinism guard, CLAUDE_CONFIG_DIR mktemp)"
---

# harness-installer — Implementation Cycle 2

## Goal

Close cycle-1's explicit Phase-7 carryover for the **Claude plugin channel**: build the content
generator that materializes `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/`
from SoT (homologous to the Codex generator), wrap `install --plugin` for Claude in the driver
(homologous to `drivers/codex.py._plugin_action`), add the verify checks, and reduce
`INSTALL_LAYOUT.md` from a manual shell recipe to a contract that references `harness install`/
`harness verify`. Also **confirm INST-OPEN-1** — decide file-by-file which hooks the Claude plugin
carries (result: `_internal/hooks_inventory.md`, adopt set = `git-state-guard.sh` +
`artifact-guard.sh`). All demonstrated under a throwaway temp `HOME` + mktemp `CLAUDE_CONFIG_DIR`
+ `--dry-run` — never touching the real `~/.claude`, `~/.claude/plugins`, `~/.codex`, or
`~/.config/opencode`.

**In-scope**: (1) Claude plugin content generator, (2) INST-OPEN-1 confirmation, (3) `install
--plugin` Claude path + verify, (4) INSTALL_LAYOUT.md reduction (INST-OPEN-3).

**Out of scope (explicit)**: OpenCode plural-dir migration (INST-OPEN-4 stays OPEN) ·
`spec/prd.md` edits (OPEN-section update is the main orchestrator's autopilot-spec update; this
plan only records **whether** an update is needed) · `dispatch-liveness.sh` changes.

## Current State Analysis (verified this worktree, branch `harness-installer-impl2`)

### Cycle-1 landed (main-merged: Phase 0~6 + Codex plugin wrap, code-test 51/51 PASS)
- `tools/install/` is a working installer: `projector.py` (symlink recipe), `manifest.py`
  (hash-manifest/drift/reapply), `drivers/{claude,codex,opencode}.py`, `verifier.py`,
  `installer.py` cmd_* wiring, `mem import` + `~/.local/bin` launchers.
- **Codex plugin channel wrapped in-cycle**: `drivers/codex.py._plugin_action` (L33-86) does
  `codex plugin marketplace add` + `codex plugin add <spec>@<marketplace>` with dry-run branch,
  CLI-absent SKIP, timeout, and a normalized action-report shape. **This is the template for the
  Claude path.**

### Claude plugin channel — cycle-1 left at skeleton (this cycle fills it)
- `drivers/claude.py` `plugin=True` currently emits **SKIP-only** (L41-49):
  `"SKIP(claude): plugin channel — deferred to next cycle (Phase 7 boundary)"`. No generator, no
  CLI wrapping. This is exactly the carryover.
- `adapters/claude/plugin-marketplace/` skeleton on disk:
  - `.claude-plugin/marketplace.json` (exists)
  - `plugins/agent-harness-claude/.claude-plugin/plugin.json` (exists — `name`/`description`/`author`)
  - `plugins/agent-harness-claude/README.md` (exists — "sync-native 생성기 산출 자리 — 손 편집 금지")
  - **Missing (to be generated)**: `skills/`, `agents/`, `hooks/`, `hooks/hooks.json`.
- **No `adapters/claude/bin/sync-native-plugin.py` yet** — Claude is the native runtime; unlike
  Codex it has no sync-native family. This cycle adds the **first** Claude sync-native generator,
  and it exists specifically to physically materialize the plugin (Claude's other surfaces are
  the repo-root SoT itself, so they need no generator; only the plugin channel needs a copy).

### Claude surfaces the plugin will carry (verified counts)
- `adapters/claude/skills/*/SKILL.md` = **28** (real dirs, not symlinks) → plugin `skills/`.
- `adapters/claude/agents/*.md` = **9** → plugin `agents/`.
- `hooks/` adopt set (INST-OPEN-1, `_internal/hooks_inventory.md`) = **2**: `git-state-guard.sh`,
  `artifact-guard.sh` → plugin `hooks/` + generated `hooks/hooks.json`.
- **`.mcp.json` absent** (neither repo root nor `adapters/claude/`) → no MCP content.
- **`bin/` not carried**: `adapters/claude/bin/` = `dispatch-headless.py` / `mem-distill-worker.sh`
  / `install-windows.sh` — all dispatch/mem/Windows family, not consumer-meaningful self-contained
  executables → skip (parallels the INST-OPEN-1 dispatch/mem exclusion).

### Claude plugin constraints (PRD §"plugin 채널 — Claude Code", verified 2026-07-12)
- **self-contained**: install copies plugin into version-ephemeral `~/.claude/plugins/cache`; a
  plugin cannot reference `../` outside its own root → **all content physically included** at
  build time (generator output, NOT hand-copy — original 3, INST-D-4; bound to SoT via `--check`).
- Path refs inside the plugin use `${CLAUDE_PLUGIN_ROOT}` (ephemeral) / `${CLAUDE_PLUGIN_DATA}`
  (`~/.claude/plugins/data/<id>/`, survives update) for persistent state.
- plugin `settings.json` honors only `agent` / `subagentStatusLine` keys → no general settings in
  plugin.json.
- plugin agents **ignore** `hooks` / `mcpServers` / `permissionMode` frontmatter → agents copied
  verbatim; those keys are inert (document, do not strip).
- skills are namespaced `/agent-harness-claude:<skill>`.

### Reusable references (read, mirror — never blind-reimplement)
- `adapters/codex/bin/sync-native-plugin.py` (168 lines) — generator skeleton (const block,
  `plugin_json`/`marketplace_json` literals, `write_json`, `sync()` copytree, `check()` +
  `check_file()`, `main()` with `--check`). Codex carries **skills only**; Claude extends to
  skills + agents + hooks + hooks.json (see `_internal/hooks_inventory.md`精读 note).
- `drivers/codex.py._plugin_action` (L33-86) — CLI-wrapping skeleton (dry-run / CLI-absent SKIP /
  timeout / blocked-on-nonzero / action-report shape).
- `tools/build-manifest.py` — `--check` drift-generator pattern the plugin generator's `--check`
  mirrors (build in memory → byte-diff → exit 1 on drift).
- `INSTALL_LAYOUT.md` (514 lines) — structure: Target Layout (1-16), Claude Projection (17-45),
  Windows (46-86), fleet CLI (87-103), Codex Projection (104-169), OpenCode Projection (170-238),
  **Migration Order (239-514, ~275 lines of manual verify steps)**. Phase 4 target.

---

## Change Plan

Phase ordering (hard deps): **Phase 1 → 2 → 3** (generator must exist before the driver wraps it
and before verify `--check`s it). Phase 4 (docs) is independent — can parallelize. Phase 5
(code-test) is last.

---

### Phase 1 — `adapters/claude/bin/sync-native-plugin.py`: Claude plugin content generator (P0)

**New file**, homologous to `adapters/codex/bin/sync-native-plugin.py` (mirror its structure; do
not invent a new shape). Executable, `python3` stdlib only (no pip).

**Step 1.1 — Constants + JSON literals.**
- `ROOT = Path(__file__).resolve().parents[3]`; `ADAPTER = ROOT/"adapters"/"claude"`;
  `PLUGIN_NAME = "agent-harness-claude"`;
  `MARKETPLACE_ROOT = ADAPTER/"plugin-marketplace"`;
  `MARKETPLACE = MARKETPLACE_ROOT/".claude-plugin"/"marketplace.json"`;
  `PLUGIN_ROOT = MARKETPLACE_ROOT/"plugins"/PLUGIN_NAME`.
- `plugin_json()` → deterministic dict (`name`, `description`, `author`; **no** general settings
  keys — only `agent`/`subagentStatusLine` would be valid and neither is needed). Regenerate the
  existing skeleton `plugin.json` byte-for-byte so `--check` binds it.
- `marketplace_json()` → `{name: "agent-harness", ...plugins:[{name: PLUGIN_NAME, source:
  {source:"...", path:"./plugins/agent-harness-claude"}, ...}]}`. **Follow the Claude Code
  marketplace.json schema** (verify against the existing skeleton `marketplace.json` + official
  `plugin-marketplaces` doc — the source form differs from Codex's `.agents/plugins/` shape).
- `HOOK_ADOPT = ["git-state-guard.sh", "artifact-guard.sh"]` (from `_internal/hooks_inventory.md`).

**Step 1.2 — `hooks_json()` literal.**
- Register the 2 adopted hooks on `PreToolUse` with plugin-relative command paths:
  `"command": "sh \"${CLAUDE_PLUGIN_ROOT}/hooks/git-state-guard.sh\""` and likewise for
  `artifact-guard.sh`. Match the `hooks.json` schema Claude expects (matcher + hooks[] with
  `type:"command"`); **verify the exact hooks.json shape against current Claude docs** before
  finalizing (runtime-currentness — the settings.json uses `$HOME/.claude/hooks/...`; the plugin
  form must be `${CLAUDE_PLUGIN_ROOT}`).

**Step 1.3 — `sync()`.**
- Guard: raise `SystemExit` if `adapters/claude/skills` or `adapters/claude/agents` missing.
- `write_json(PLUGIN_ROOT/".claude-plugin"/"plugin.json", plugin_json())`.
- `write_json(MARKETPLACE, marketplace_json())`.
- Copy content (rmtree-then-copytree so hand-edits are erased — original 3):
  - `PLUGIN_ROOT/"skills"` ← `ADAPTER/"skills"` (copytree).
  - `PLUGIN_ROOT/"agents"` ← `ADAPTER/"agents"` (copytree — verbatim; inert frontmatter keys OK).
  - `PLUGIN_ROOT/"hooks"/<name>` ← `ROOT/"hooks"/<name>` for each `HOOK_ADOPT` (copy2, preserve
    exec bit).
  - `write_json(PLUGIN_ROOT/"hooks"/"hooks.json", hooks_json())`.
- Preserve `README.md` (do not delete — it documents the generated-content policy).

**Step 1.4 — `check()` + `check_file()`** (mirror codex L102-152).
- plugin.json / marketplace.json / hooks.json byte-equal to their literals.
- Each `adapters/claude/skills/*/SKILL.md` == plugin copy; each `adapters/claude/agents/*.md` ==
  plugin copy; each adopted `hooks/<name>` == plugin copy.
- **Excess-file detection**: any file under `PLUGIN_ROOT/{skills,agents,hooks}` not in the
  expected set → stale (catches deletions from SoT + stray hand-edits).
- Print `stale[]` to stderr, `return 1` if any, else `return 0`.

**Step 1.5 — `main()`**: `--check` → `check()`, else `sync()` + success print. Return code
propagated via `raise SystemExit(main())`.

- **Done when**: `python3 adapters/claude/bin/sync-native-plugin.py` materializes
  `plugins/agent-harness-claude/{skills(28),agents(9),hooks(2)+hooks.json,.claude-plugin/plugin.json}`;
  immediate re-run is byte-identical (idempotent); `--check` exits 0 on a clean tree and exits 1
  after touching any generated file. **No file outside `adapters/claude/plugin-marketplace/`
  is written.**

---

### Phase 2 — `drivers/claude.py`: `install --plugin` Claude wrapping (P0)

**Target**: `tools/install/drivers/claude.py`. Replace the SKIP-only `plugin` branch (L41-49) with
a real `_plugin_action(dry_run)`, homologous to `drivers/codex.py._plugin_action`.

**Step 2.1 — `_plugin_action(dry_run)`** (new, mirror codex L33-86).
- Module constants: `_MARKETPLACE_SOURCE_RELPATH = "adapters/claude/plugin-marketplace"`,
  `_MARKETPLACE_NAME = "agent-harness"`, `_PLUGIN_SPEC = "agent-harness-claude@agent-harness"`.
- `marketplace_source = str(paths.resolve_source(_MARKETPLACE_SOURCE_RELPATH))`.
- `marketplace_cmd = ["claude", "plugin", "marketplace", "add", marketplace_source]` and
  `plugin_cmd = ["claude", "plugin", "install", _PLUGIN_SPEC]` — **verify the non-interactive CLI
  verbs/flags against the current `claude plugin` CLI** (runtime-currentness; PRD confirms
  `marketplace add` + `plugin install` non-interactive). Add `--json`/non-interactive flag only
  if the live CLI supports it.
- `dry_run` → `status:"planned"`, `detail` = the two command strings; no subprocess.
- `shutil.which("claude") is None` → `status:"skipped"`, SKIP detail (parity-loss line).
- Run marketplace add (timeout=60, capture_output); returncode≠0 or FileNotFound/Timeout →
  `status:"blocked"`. Then plugin install, same handling. Success → `status:"registered"`.

**Step 2.2 — wire into `install()`.**
- Replace L41-49 SKIP block: `if plugin: actions.append(_plugin_action(dry_run))`.
- **INST-D-5 parity**: keep the symlink + copy_once projection running even when `plugin=True` —
  the plugin cannot carry settings.json copy / statusline / mem restore / CLAUDE.md / PATH
  launcher (plugin honors only `agent`/`subagentStatusLine`). "plugin ⇒ skip symlink" is an
  explicit anti-pattern (mirror codex docstring).
- `blocked` aggregation already covers the new action (`any(status=="blocked")`).

- **Done when**: `harness install claude --plugin --dry-run --json` prints planned `claude plugin
  marketplace add <path>` + `claude plugin install agent-harness-claude@agent-harness` **and** the
  full symlink/copy_once plan; with `claude` CLI absent, a real (non-dry-run) `--plugin` run
  emits the SKIP line instead of erroring; symlink projection is present in both cases.

---

### Phase 3 — `drivers/claude.py` `checks()` + verifier: plugin verify checks (P0)

**Target**: `drivers/claude.py.checks()` (extend) — reuse `verifier.check_cmd` /
`check_file_exists` (no verifier core change; it already iterates callables).

**Step 3.1 — generator drift check.**
- `verifier.check_cmd("claude.sync-native-plugin", ["python3",
  "adapters/claude/bin/sync-native-plugin.py", "--check"], cwd=agent_home)` — asserts the
  generated plugin content is not stale vs SoT (SoT↔generator binding, original 3 / INST-D-4).

**Step 3.2 — marketplace source presence check.**
- `verifier.check_file_exists("claude.plugin-marketplace-source",
  <resolve_source>/adapters/claude/plugin-marketplace/.claude-plugin/marketplace.json)` — mirrors
  the codex `codex.plugin-marketplace-source` check.

**Step 3.3 — plugin registration/install verify (CLI-gated, read-only).**
- A `_plugin_registered()` callable: if `claude` CLI absent →
  `{ok:True, detail:"SKIP(claude): plugin registration — claude CLI absent"}`; else read-only
  query (`claude plugin marketplace list` / `claude plugin list` — **verify the exact read-only
  subcommand against the live CLI**) and check `agent-harness` marketplace + `agent-harness-claude`
  plugin appear. **Must be read-only** (never install during verify) and **must target a
  temp/isolated config** in tests (see Phase 5 isolation contract §4). Under the real home during
  a genuine `verify`, the query is read-only so it is safe, but tests use mktemp
  `CLAUDE_CONFIG_DIR`.

- **Done when**: `harness verify claude --json` returns checks including
  `claude.sync-native-plugin` (exit 0 on clean tree), `claude.plugin-marketplace-source`, and the
  CLI-gated registration check (SKIP when `claude` absent); all read-only, no disk mutation.

---

### Phase 4 — `INSTALL_LAYOUT.md` reduction (INST-OPEN-3, P1)

**Target**: `INSTALL_LAYOUT.md`. **Re-narrate, do NOT delete** (PRD §3 대응-동기화 / INST-OPEN-3).
Preserve every contract-level fact; replace the copy-pasteable shell enumerations + the manual
Migration Order battery with a contract statement that points at `harness install` / `harness
verify`.

**Step 4.1 — Projection sections (Claude 17-45, Codex 104-169, OpenCode 170-238).**
- Keep: the **why/contract** — e.g. the copy-once rationale ("settings.json is runtime-owned,
  copy once, never re-link — an atomic settings write would replace a symlink and pollute the
  repo", L29-35), Windows symlink→copy + HOME-injection specifics (46-86), Codex's "plugin cannot
  carry agents .toml / prompts / config fragment → symlink projection still required" note,
  OpenCode's non-destructive-merge + plural-dir drift (INST-OPEN-4) caveat.
- Replace: the literal `ln -sfn $AGENT_HOME/..._setting/$p ~/.<rt>/$p` recipe lists → one line
  "이 배선은 `harness install [claude|codex|opencode]` 이 기계화한다 (수동 `ln -sfn` 나열 대체)"
  + a pointer to the surface×channel matrix in the PRD. Keep a short table of *what maps where*
  (contract) but not the runnable command list.

**Step 4.2 — Migration Order block (239-514).**
- Replace the ~275-line manual verification battery with: "이 검증 절차는 `harness verify
  [runtime]` 이 기계화했다 (check 목록 = 각 driver `checks()`; exit code 0/2 로 판정)." Keep any
  *contract-level* invariant that is NOT a runnable step (e.g. the BLOCKED-on-active-process
  safety rule, exit-code semantics) as prose, and reference `harness verify --json` for the
  machine output.
- Keep the fleet CLI section (87-103) — it documents the `~/.local/bin` launcher contract, still
  valid.

**Step 4.3 — 대응 동기화.**
- Add a short header note: "수동 레시피·검증은 `harness install`/`harness verify` 로 대체됨 (PRD
  harness-installer, cycle 1~2). 본 문서는 계약 서술만 유지." (§3 correspondence-sync — part of
  the change, no separate confirm.)
- **This is a user-read doc** → after the rewrite, the code-report stage should route it through
  the editorial team polish pass (Korean 재서술 quality). Note in code-report handoff.

- **Done when**: `INSTALL_LAYOUT.md` has no copy-pasteable per-runtime `ln -sfn` recipe list and
  no manual Migration Order step battery, but retains Target Layout, copy-once rationale, Windows
  specifics, Codex/OpenCode特기, fleet contract, exit-code semantics, and INST-OPEN-4 caveat, each
  pointing at `harness install`/`harness verify`.

---

### Phase 5 — code-test (⚠️ isolation contract — MANDATORY, cycle-1 incident-driven)

Cycle 1 corrupted the real `~/.claude/settings.json` because `HOME`/`AGENT_HOME`/`MEM_STORE`
exports were lost across separate Bash calls (each Bash call resets shell state), so a drift-
injection line hit the real `$HOME` instead of a mktemp temp HOME
(`_internal/dev_reviews/INCIDENT_real_home_touched.md`). The code-test stage **must** enforce:

1. **Single self-contained script per temp-HOME scenario.** Every temp-HOME test sets
   `HOME`/`AGENT_HOME`/`MEM_STORE` (and `CLAUDE_CONFIG_DIR`, below) **at the very top, inside one
   script** under `plans/2026-07-13_harness-installer-impl2/_internal/test_scripts/*.sh`, run in a
   **single** Bash invocation. **Never** attempt to carry an `export` across Bash-call boundaries.
2. **Explicit target-root args only.** installer/generator commands take an explicit mktemp target
   root; **never bare `$HOME`**. The generator (Phase 1) writes only under
   `adapters/claude/plugin-marketplace/` — its `--check` is repo-read-only and needs no temp HOME,
   but the `sync()` write test runs against a **copied temp checkout** or asserts the write set is
   confined to the marketplace subtree.
3. **Determinism guard baked into each script.** Before switching to temp HOME, capture sha256 of
   the real `~/.claude/settings.json`, `~/.codex/config.toml`,
   `~/.config/opencode/opencode.json`; a `trap` on EXIT re-asserts they are unchanged (byte-
   identical) — the script fails loudly if any real config moved.
4. **Real `claude plugin` CLI tests use a mktemp `CLAUDE_CONFIG_DIR` only.** Any test that invokes
   the live `claude plugin marketplace add` / `plugin install` / `plugin list` points
   `CLAUDE_CONFIG_DIR` (mktemp) at a throwaway dir — **never** install/register into the real
   `~/.claude/plugins`. Gate behind `claude` CLI presence; SKIP (not fail) when absent. Also guard
   the real `~/.claude/plugins` sha/mtime in the trap.

**Graduated levels to reach**: syntax (`py_compile` the new generator + edited driver) → import →
smoke (`sync-native-plugin.py --check`; `harness install claude --plugin --dry-run --json`) →
functional (generator `sync()` into a confined temp checkout → `--check` clean → touch a generated
file → `--check` exit 1 → regenerate → clean; `harness verify claude --json` includes the new
checks; `--plugin` dry-run prints both CLI commands + symlink plan; CLI-absent SKIP path) →
(CLI-gated, if `claude` present) integration under mktemp `CLAUDE_CONFIG_DIR`: marketplace add +
plugin install + registration verify, then teardown.

- **Done when**: all levels pass, the real-home determinism trap holds (real configs +
  `~/.claude/plugins` byte-unchanged), and no test wrote outside a mktemp dir or the repo
  marketplace subtree.

---

## Risks

- **claude plugin CLI surface drift**: the exact non-interactive verbs/flags (`marketplace add`,
  `plugin install`, read-only `list`) and `hooks.json` schema must be **verified against the live
  `claude` CLI + current docs** (runtime-currentness gate), not assumed from the Codex analogue —
  Claude's marketplace.json source form and CLI verbs differ from Codex's. code-execute confirms
  before finalizing command arrays. If the CLI is absent in the dev env, the wrapping is exercised
  via dry-run only + a documented SKIP (parity-loss line), and the CLI-live path is asserted by
  the isolated `CLAUDE_CONFIG_DIR` test when available.
- **Codex-vs-Claude generator divergence (do not over-mirror)**: Codex carries **skills only**;
  Claude carries skills + agents + **hooks + hooks.json**. Blindly copying the Codex generator
  would omit agents/hooks. The `check()` excess-file logic must cover all three content trees, not
  just skills.
- **self-contained violation**: any plugin path that resolves outside `PLUGIN_ROOT` (a `../`
  reference, or an agent frontmatter pointing at repo tools) breaks the cache model. hooks.json
  must use `${CLAUDE_PLUGIN_ROOT}`; agents' inert `hooks`/`mcpServers` frontmatter is ignored by
  Claude (safe) but must not be relied upon.
- **INST-OPEN-1 defer set**: spec-skill-gate + spec-read-marker + spec-sync-nudge are deferred
  because they write grounding state into `$AGENT_HOME` and would need `${CLAUDE_PLUGIN_DATA}`
  rebasing — a scope expansion. Recorded in `_internal/hooks_inventory.md`; revisit only if
  consumer spec-pipeline support is requested.
- **INSTALL_LAYOUT.md is a user-read doc**: the Phase-4 rewrite must preserve every contract fact
  (deletion, not reduction, is the failure mode) and should be polished by the editorial team in
  code-report.
- **Real-home corruption (cycle-1 incident class)**: mitigated structurally by the Phase-5
  isolation contract (single-script env, mktemp targets, determinism trap, mktemp
  `CLAUDE_CONFIG_DIR`). This is the single most important safety constraint of the cycle.

## PRD OPEN-section status (for code-report — this stage does NOT edit prd.md)

- **INST-OPEN-1**: **closeable** — file-level hook adopt/exclude is now decided
  (`_internal/hooks_inventory.md`: adopt `git-state-guard.sh` + `artifact-guard.sh`; defer the
  spec-pipeline trio; exclude memory/statusline/dispatch families + core-first/marker +
  design-postwrite). code-report records that the PRD OPEN entry can move to 확정, with the actual
  prd edit performed by the main orchestrator's autopilot-spec update.
- **INST-OPEN-3**: **closeable** after Phase 4 lands — `INSTALL_LAYOUT.md` reduced to contract +
  `harness install`/`verify` reference. code-report notes the PRD OPEN entry can close.
- **INST-OPEN-4** (OpenCode plural-dir migration): **stays OPEN** — untouched this cycle (out of
  scope).

## Verification (orientation only — code-test authors the actual isolated scripts per Phase 5)

All temp-HOME/CLI commands run from a **single self-contained script** with mktemp
`HOME`/`AGENT_HOME`/`MEM_STORE`/`CLAUDE_CONFIG_DIR` set at the top + a determinism trap (Phase 5).
Representative checks:

- `python3 adapters/claude/bin/sync-native-plugin.py --check` → exit 0 clean, exit 1 after edit.
- generator `sync()` (in a confined temp checkout) materializes skills(28)/agents(9)/hooks(2)+
  hooks.json/plugin.json; re-run byte-identical.
- `harness install claude --plugin --dry-run --json` → planned `claude plugin marketplace add` +
  `plugin install` + full symlink/copy_once plan.
- `harness verify claude --json` → includes `claude.sync-native-plugin`,
  `claude.plugin-marketplace-source`, CLI-gated registration check.
- (if `claude` present) mktemp `CLAUDE_CONFIG_DIR`: marketplace add + install + read-only
  registration verify, teardown.
- **Safety assertion (must hold throughout)**: real `~/.claude/settings.json`, `~/.codex/config.toml`,
  `~/.config/opencode/opencode.json`, and `~/.claude/plugins` are byte-unchanged after every run.
