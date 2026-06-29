# Adaptation Inventory

This is the working inventory for turning the historical Claude Code setting
into a portable agent setting plus runtime adapters.

## Status Classes

| Status | Meaning |
|---|---|
| `portable` | Can be consumed by multiple runtimes as-is. |
| `adapter-native` | Belongs to one runtime adapter. |
| `projection` | Versioned mirror into a runtime home; symlink/generated only. |
| `compat-passthrough` | Still shared because Claude Code currently consumes it directly. |
| `needs-split` | Must be separated into portable source plus adapter-native realization. |

## Current Surfaces

| Surface | Current location | Status | Target split |
|---|---|---|---|
| Core operating contract | `core/CORE.md`, `core/WORKFLOW.md`, `core/CONVENTIONS.md`, `core/OPERATIONS.md`, `core/MEMORY.md`, `core/DESIGN_PRINCIPLES.md` | portable | Keep concrete runtime names out unless documenting adapter mapping. |
| Adapter boundary | `core/ADAPTATION.md`, `adapters/*/ADAPTATION.md` | portable / adapter-native | Single source for what symlink means and what still needs adaptation. |
| Claude bootstrap | `adapters/claude/CLAUDE.md` | adapter-native | Keep Claude Code response, routing, hook, statusline, and command rules here. |
| Codex bootstrap | `adapters/codex/AGENTS.md` | adapter-native | Expand only with behavior that Codex can actually perform. |
| Codex preflight wrappers | `adapters/codex/bin/preflight.sh`, `role-map.sh`, `capability-map.sh`, `mode-map.sh`, `distill-worker.sh` | adapter-native | Executable Codex bridge for hook invariants, portable role mapping, capability realization, mode support classification, and distill proposals. |
| Claude settings/hooks registration | `adapters/claude/settings.json` | adapter-native | Codex must get wrapper/preflight equivalents, not this JSON. |
| Slash commands | `adapters/claude/commands/` | adapter-native | Future runtimes need native command wrappers or instruction entries. |
| Portable capability catalog | `capabilities/README.md`, `capabilities/*.md` | portable | Per-capability specs define runtime-neutral contracts; Codex resolves entries through `adapters/codex/bin/capability-map.sh`. |
| Claude skills | `adapters/claude/skills/*/SKILL.md` | adapter-native projection, compat-content | Concrete Claude Skill files preserve current Claude behavior while portable contracts grow under `capabilities/`. |
| Portable role catalog | `roles/README.md` | portable | Grow into per-role specs when adapter parity work needs finer granularity; Codex currently resolves concrete runtime settings through `adapters/codex/bin/role-map.sh`. |
| Role mode inventory | `roles/MODES.md` | portable | Classifies shared `roles/modes/` prompt fragments by portability; Codex currently enforces the classification through `adapters/codex/bin/mode-map.sh`. |
| Claude agents | `adapters/claude/agents/*.md` | adapter-native | Preserve Claude Agent frontmatter/model/tool schema while realizing `roles/README.md`. |
| Agent modes | `adapters/claude/agent-modes/*/*.md`, shared `roles/modes/*.md` | adapter-native projection, mixed content | Concrete Claude mode files preserve current behavior while `roles/MODES.md` classifies portability; split adapter-coupled design/verification/tool notes when Codex-native modes exist. |
| Hook invariant catalog | `core/HOOKS.md` | portable | Names hook-level invariants and classifies current scripts. |
| Hook scripts | `adapters/claude/hooks/*.sh`, shared `hooks/*.sh` | adapter-native projection, mixed content | Concrete Claude hook files preserve current behavior while splitting invariant checks from runtime hook payload wrappers. |
| Memory distiller | `hooks/mem-distill-dispatch.sh`, `tools/memory/` | mixed | Keep DB/CLI portable; move session log reader and model invocation to adapters. |
| Agent notes root | `<agent-notes-root>` | runtime/continuity state | Portable docs define the layer and required queues; data is not harness source and must not be committed here. Adapter docs own concrete local path realizations. |
| Worklog board app | `<worklog-board-app>` plus `<worklog-board-app>-wt/` worktrees | local app workspace / needs-split if promoted | Treat current code, DB/cache, build output, dispatch logs, env files, and worktrees as external to this harness. If promoted later, split source into a separate app repo or portable tool first. Adapter docs own concrete local path realizations. |
| Worklog status helper | `utilities/agent-worklog-state.sh`, Codex `preflight.sh worklog` | portable helper + adapter wrapper | Read-only inventory of configured notes root and board app; no data migration or mutation. |
| Design MCP | `tools/design-mcp/`, design skills | mixed | Keep render/check semantics portable; move Claude MCP registration paths to adapter docs. |
| Utility scripts | `adapters/claude/utilities/*`, shared `utilities/*` | adapter-native projection, mixed content | Concrete Claude utility files preserve current behavior while runtime-neutral helper behavior remains available from the shared utility layer. |
| Scaffold assets | `adapters/claude/scaffolds/*`, shared `scaffolds/*` | adapter-native projection, mixed content | Concrete Claude scaffold files preserve current behavior while portable template intent remains available from the shared scaffold layer. |
| Loop helpers | `adapters/claude/loops/*`, shared `loops/*` | adapter-native projection, mixed content | Concrete Claude loop files preserve current drill/oncall/study behavior while runtime-coupled loop invocation remains classified for future adapters. |
| Tool helpers | `adapters/claude/tools/*`, shared `tools/*` | adapter-native projection, mixed content | Concrete Claude tool files preserve current helper behavior while memory/session/runtime-specific assumptions are split behind adapter or tool plugin boundaries. |
| Projection directories | `claude_setting/`, `codex_setting/` | projection | Must contain only symlinks or generated adapter output. |

## Migration Order

1. **Role vocabulary first**: replace portable docs' concrete model names with
   `fast reviewer`, `deep reviewer`, `external adversary`, and related roles.
   Adapter docs own concrete model names and CLI-specific choices.
2. **Capability specs second**: keep portable capability meaning in
   `capabilities/`; keep Claude Skill syntax in generated or maintained
   `adapters/claude/skills/<name>/SKILL.md` files. Codex must pass through
   `capability-map.sh`, not `skills/*/SKILL.md`.
3. **Agent profiles third**: keep portable role meaning in `roles/`; keep
   concrete frontmatter/model/tool mapping in adapter-native agent files. Codex
   must pass through `role-map.sh` and `mode-map.sh` for runtime decisions.
4. **Hook payloads fourth**: keep invariant semantics in `core/HOOKS.md`, then
   isolate Claude event JSON, statusline JSON, ScheduleWakeup, and MCP
   registration behind adapter-native wrappers.
5. **Projection last**: after a surface has an adapter-native realization,
   update `claude_setting/` or `codex_setting/` to point at that adapter output.

## Acceptance Tests

A surface is not considered adapted until all of the following are true:

- The portable document can be read without knowing Claude Code file formats.
- The Claude adapter still exposes the old runtime path and behavior.
- The Codex adapter either exposes an equivalent behavior or explicitly marks
  the behavior unsupported with fallback instructions.
- Concrete model/runtime names appear only in adapter-native files, tests, or
  legacy compatibility notes.
- `claude_setting/` and `codex_setting/` remain projections, not independent
  semantic sources.
