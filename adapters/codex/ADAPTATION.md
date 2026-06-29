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
| Shared helper tools | `tools/`, `utilities/` | projected selectively |

## Explicit Non-Support

Codex must not consume these Claude-native files as native configuration:

| Claude-native surface | Codex status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; Codex needs wrapper/preflight equivalents |
| `adapters/claude/commands/` | Not consumable; Codex commands must be expressed as AGENTS instructions or wrapper commands |
| `adapters/claude/statusline.sh` | Not consumable; input schema is Claude statusline JSON |
| `adapters/claude/track-toggle.sh` | Semantics reusable, implementation depends on Claude session id fallback |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; Codex should start from `roles/README.md` |

## Required Codex Mappings

| Portable invariant | Codex adaptation requirement |
|---|---|
| artifact order | Run `hooks/artifact-guard.sh` through wrapper/pre-write checks where possible |
| git state safety | Run `hooks/git-state-guard.sh` before edits |
| spec read gate | Enforce through AGENTS instructions and wrapper checks; no native hook assumed |
| workflow signal | Provide explicit session reminder or wrapper output; no statusline assumption |
| memory inject/recall | Use `tools/memory/mem.py` directly; session log ingestion needs a Codex session adapter |
| memory distill | Disabled until a Codex session source and no-tools distiller contract are implemented |
| role profiles | Read `roles/README.md`, then translate roles to Codex model/reasoning-effort settings |
| capabilities | Read portable capability semantics; do not assume Claude Skill invocation |

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
`AGENTS.md`, `README.md`, `core/`, `tools/`, and `utilities/`, but must not expose
Claude-native `settings.json`, `commands/`, or `statusline.sh` as if Codex could
consume them.
