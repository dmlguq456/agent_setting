# Codex Adaptation

This adapter is not yet behavior-equivalent to the Claude Code adapter.
It defines the required mapping so Codex support can be built without copying
Claude-specific assumptions into the common core.

## Native Codex Surfaces

| Codex runtime surface | Adapter source | Projection |
|---|---|---|
| Session bootstrap | `adapters/codex/AGENTS.md` | `codex_setting/AGENTS.md` |
| Adapter guide | `adapters/codex/README.md` | `codex_setting/README.md` |
| Common contract | `core/` | `codex_setting/core` |
| Capability catalog | `capabilities/` | `codex_setting/capabilities` |
| Preflight wrappers | `adapters/codex/bin/` | `codex_setting/bin` |
| Shared helper tools | `tools/`, `utilities/` | projected selectively |

## Explicit Non-Support

Codex must not consume these Claude-native files as native configuration:

| Claude-native surface | Codex status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; Codex needs wrapper/preflight equivalents |
| `adapters/claude/commands/` | Not consumable; Codex commands must be expressed as AGENTS instructions or wrapper commands |
| `skills/*/SKILL.md` | Compatibility reference only; Codex should start from `capabilities/README.md` |
| `adapters/claude/statusline.sh` | Not consumable; input schema is Claude statusline JSON |
| `adapters/claude/track-toggle.sh` | Semantics reusable, implementation depends on Claude session id fallback |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; Codex should start from `roles/README.md` |
| `agent-modes/design/*` | Compatibility reference only until Codex has an equivalent visual/browser verification harness |

## Required Codex Mappings

| Portable invariant | Codex adaptation requirement |
|---|---|
| artifact order | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| git state safety | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits |
| memory write guard | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | Run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | Run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| workflow signal | Run `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` as explicit prompt/session reminder; no statusline assumption |
| memory inject | Run `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text session-start memory injection |
| memory recall | Run `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` before prompt handling when no automatic prompt hook is attached |
| oncall briefing | Run `adapters/codex/bin/preflight.sh briefing [cwd]` before prompt handling on the dedicated agent desk |
| memory distill | Transcript delta extraction exists via `adapters/codex/bin/preflight.sh distill-delta <session-id>`; automatic no-tools worker remains disabled until Codex has a headless worker contract |
| role profiles | Read `roles/README.md`, then translate roles to Codex model/reasoning-effort settings |
| role modes | Read `roles/MODES.md`; treat adapter-coupled modes as unsupported unless wrappers exist |
| hook invariants | Read `core/HOOKS.md`; run explicit preflight wrappers until Codex-native hook events exist |
| capabilities | Read `capabilities/README.md`; do not assume Claude Skill invocation |

## Model Mapping

Codex should expose concrete choices through environment or config:

```text
AGENT_MODEL_FAST
AGENT_MODEL_DEEP
AGENT_MODEL_EXTERNAL
AGENT_REASONING_FAST
AGENT_REASONING_DEEP
```

Until those are implemented, Codex uses the portable role names and reports any
unavailable role explicitly.

## Current Projection Boundary

`codex_setting/` should remain minimal until adapted surfaces exist. It may expose
`AGENTS.md`, `README.md`, `core/`, `capabilities/`, `bin/`, `tools/`, and
`utilities/`, but must not expose Claude-native `settings.json`, `commands/`,
`skills/`, or `statusline.sh` as if Codex could consume them.
