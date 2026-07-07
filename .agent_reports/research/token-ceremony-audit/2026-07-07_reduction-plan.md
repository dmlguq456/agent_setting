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

Recommended design:

1. Make runtime projection choose one active skill discovery path.
2. Default should be plugin-first when the plugin is installed, because plugin namespacing avoids collision with personal skills and is the shareable distribution path.
3. Keep `$CODEX_HOME/agent-skills` as a read-only pointer for inspection, but do not symlink every skill into `$CODEX_HOME/skills` when plugin mode is active.
4. Add `install-runtime-projection.sh --skills-mode native|plugin|both` with default `native` unless `--install-plugin` is passed; then default `plugin`.
5. Update `check-runtime-projection.sh` to report `check=skill-discovery:plugin|native|duplicate-warning` instead of hard-failing when per-skill symlinks are intentionally absent in plugin mode.

### P2 — Shorten always-visible descriptions

Problem: skill metadata descriptions are the always-on part. Claude skill metadata projection is about 14.7k chars; Codex duplicate metadata is worse when both surfaces are installed.

Recommended design:

- Cap each skill description to one trigger sentence plus one negative boundary when needed.
- Move examples, stage details, QA policy, artifacts, and mode tables into `references/` loaded only by selected mode/intensity.
- Add a metadata budget check: warn at 8k chars for Codex active skill surface; warn at 10k chars for Claude visible metadata.

### P3 — Thin Claude autopilot bodies

Problem: Claude `autopilot-code/SKILL.md` is 36.2k chars versus Codex 8.4k chars. All Claude skill bodies total about 545k chars, so selected monolithic skills are still expensive.

Recommended design:

- Use Codex style as target: entry skill = router + compact stage contract.
- Split deep policy into `references/intensity.md`, `references/spec-impact.md`, `references/app-mode.md`, and `references/recovery.md`.
- Preserve current behavior by requiring the selected reference reads at the relevant stage, not at skill load.

### P4 — Add deterministic footprint guard

Recommended script: `tools/context-footprint.py`.

Checks:

- bootstrap file chars (`AGENTS.md`, `CLAUDE.md`);
- active skill metadata chars by adapter;
- duplicate skill names across Codex native/plugin active surfaces;
- sample hook outputs for memory/mode/recall/briefing;
- top 10 largest selected skill bodies.

Use it as a report/warn tool first, not a failing CI gate, until thresholds stabilize.
