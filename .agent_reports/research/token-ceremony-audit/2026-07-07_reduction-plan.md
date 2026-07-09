# Context Reduction Plan — 2026-07-07

Basis: `2026-07-07_context-footprint.md` measurement.

## Priority Order

### P0 — Stop surprise per-turn spikes

Status: applied in this change set.

- Narrow `mem-briefing-inject` from `cwd == AGENT_HOME` to `cwd == ${MEM_BRIEFING_DESK:-$HOME/.claude}`.
- Keep explicit override via `MEM_BRIEFING_DESK` for a deliberate oncall discussion desk.
- Expected effect: normal `agent_setting` coding/review sessions no longer receive the 4-5k char daily oncall briefing automatically.
- Risk: users who intentionally used `agent_setting` as the oncall desk must set `MEM_BRIEFING_DESK=/home/Uihyeop/agent_setting` or open the runtime desk.

### P1 — Remove Codex duplicate skill exposure

Problem: Codex projects the same 28 harness skills through both `$CODEX_HOME/skills/<name>` and the installed `agent-harness-codex` plugin. Local metadata is about 7.1k chars, plugin metadata about 8.4k chars, combined about 15.5k chars before runtime truncation.

Status: applied in this change set.

Implemented design:

1. Runtime projection now chooses one active skill discovery path.
2. Default remains `native` for compatibility; when `--install-plugin` is passed and `--skills-mode` is omitted, default is `plugin`.
3. `$CODEX_HOME/agent-skills` remains a read-only pointer for inspection, while plugin mode removes only harness-owned `$CODEX_HOME/skills/<name>` symlinks.
4. `install-runtime-projection.sh --skills-mode native|plugin|both` is supported.
5. `check-runtime-projection.sh` reports `check=skill-discovery:native`, `check=skill-discovery:plugin`, or a native duplicate warning when the plugin is also installed.

### P2 — Shorten always-visible descriptions

Problem: skill metadata descriptions are the always-on part. Claude skill metadata projection was about 14.7k chars; Codex duplicate metadata was worse when both surfaces were installed.

Status: applied in this change set.

Implemented design:

- Codex/OpenCode generated Skill descriptions now contain only `Use for <identifier>: <portable meaning>`.
- Claude adapter and root compatibility Skill descriptions now use the existing compact `metadata.blurb` field.
- Current metadata footprint after P1/P2: Codex local 3,501 chars, Codex plugin 4,845 chars, OpenCode 3,585 chars, Claude 2,834 chars (name+description+path estimate).
- Deterministic budget enforcement is folded into P4's `tools/context-footprint.py` guard.

### P3 — Thin Claude autopilot bodies

Problem: Claude `autopilot-code/SKILL.md` was 44.4k chars after recent policy additions, versus Codex 8.6k chars. Selected monolithic skills are still expensive even when metadata is short.

Status: applied in this change set for `autopilot-code`.

Implemented design:

- Claude/root `autopilot-code/SKILL.md` is now a 4.1k-char router + compact stage contract.
- Deep policy moved into direct references: `context-and-guards.md`, `arguments-and-decisions.md`, `dev-pipeline.md`, `debug-audit.md`, and `pipeline-summary-safety.md`.
- The router explicitly tells the agent which reference to read for each mode/stage, preserving behavior with progressive disclosure.

### P4 — Add deterministic footprint guard

Status: applied in this change set.

Implemented script: `tools/context-footprint.py`.

Checks:

- bootstrap file chars (`AGENTS.md`, `CLAUDE.md`, OpenCode `AGENTS.md`);
- skill metadata chars by adapter;
- active Codex native/plugin runtime exposure and duplicate skill names;
- sample hook/preflight outputs for mode, recall, and briefing;
- top 10 largest selected Skill bodies.

It is report/warn by default and exits 0. Use `--strict` only when warnings should fail a check. Test fixtures use `--skip-runtime --skip-hooks` for deterministic metadata-only validation.

## Follow-up — 2026-07-09

### P1 runtime switch applied

Local `$CODEX_HOME` switched to plugin-only skill discovery via `install-runtime-projection.sh --skills-mode plugin` (28 native symlinks removed, plugin kept). `context-footprint.py` now reports `codex_active_surfaces=plugin chars=5629 duplicate_names=0`, warnings 0.

### P3 extended to all remaining large Claude skill bodies

Branch `skill-p3-split` (96b61db) splits the 12 remaining >20k Claude skills (draft/research/lab/note/refine/spec, analyze-user/project, sync-skills, draft-strategy, audit, post-it) into thin routers plus `references/*.md`. Frontmatter unchanged, content moved verbatim by line slice (zero heading/non-blank-line loss), root `skills/` mirror byte-equivalent. Selected-load fixed cost for the 12 skills: 481k -> 108k chars (-77%); largest remaining Claude body 17.9k. All gates pass (adaptation-boundary, sync-native --check x3, manifest --check, portable-guards, footprint warnings 0).

### P5 — CLAUDE.md always-on dedup (this change set)

`adapters/claude/CLAUDE.md` Drift-Free Essentials artifact table / scope bullets / flag list and the memory/profile Source-of-Truth prose were derived duplication of `core/CONVENTIONS.md` §5 (single source, "재정의 금지"), `core/WORKFLOW.md`, and `core/MEMORY.md` §7. Replaced with single-source pointers; update-trigger policy synced.

### P6 — AGENTS.md diet is guard-coupled (deferred, needs decision)

`adapters/codex/AGENTS.md` (19.0k) cannot be meaningfully reduced without a guard-spec change: 42 pinned "must document" assertions in `check-adaptation-boundary.sh` cover 13.1k chars (the per-capability tool-contract bullets), and the unpinned 5.9k remainder is the irreducible bootstrap skeleton (source order, currentness gate, response policy, compatibility boundary). A real diet means moving pinned bullets to an on-demand reference doc and re-pointing those assertions — exposed as a design decision rather than applied silently.
