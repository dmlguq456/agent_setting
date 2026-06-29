# Claude Code Adaptation

This adapter preserves the previous Claude Code setting behavior while moving
runtime-specific files out of the common root.

## Native Claude Surfaces

| Claude runtime surface | Adapter source | Projection |
|---|---|---|
| Session bootstrap | `adapters/claude/CLAUDE.md` | `claude_setting/CLAUDE.md` |
| Hook and permission config | `adapters/claude/settings.json` | `claude_setting/settings.json` |
| Keybindings | `adapters/claude/keybindings.json` | `claude_setting/keybindings.json` |
| Slash commands | `adapters/claude/commands/` | `claude_setting/commands` |
| Agents | `adapters/claude/agents/` | `claude_setting/agents` |
| Statusline | `adapters/claude/statusline.sh` | `claude_setting/statusline.sh` |
| `/track` implementation | `adapters/claude/track-toggle.sh` | `claude_setting/track-toggle.sh` |

`~/.claude/*` should point at `claude_setting/*`, not directly at common files.

## Compatibility Passthrough

These surfaces are still consumed by Claude Code directly, but are not yet clean
portable sources:

| Surface | Current projection | Why passthrough is allowed for now | Required split |
|---|---|---|---|
| Skills | `claude_setting/skills -> ../skills` | Existing files are Claude Skill format and preserve old behavior | Grow `capabilities/` into per-capability specs, then generate or maintain `adapters/claude/skills` |
| Agent modes | `claude_setting/agent-modes -> ../agent-modes` | Mode docs are prompt fragments used by current agents | Classify as portable role modes or Claude-native mode prompts |
| Hooks | `claude_setting/hooks -> ../hooks` | Shell scripts are wired by Claude settings and preserve old behavior | Split portable invariant scripts from Claude hook-payload wrappers |
| Utilities | `claude_setting/utilities -> ../utilities` | Mostly runtime-neutral helper scripts | Move Claude-only helpers to adapter if found |
| Tools | `claude_setting/tools -> ../tools` | CLI tools are mostly runtime-neutral; some memory/session assumptions remain | Isolate Claude session adapters under adapter or tool plugin |

Compatibility passthrough is a temporary migration state, not the final adapter
shape.

Agent files have completed the first split: portable role meaning is summarized
in `roles/README.md`, while Claude Agent frontmatter, tool lists, and concrete
model mapping live in `adapters/claude/agents/`.

Capability files have started the same split: portable capability meaning is
summarized in `capabilities/README.md`, while current Claude Skill mechanics
remain in `skills/*/SKILL.md` as compatibility passthrough.

## Model Mapping

Claude Code maps portable roles as follows:

| Portable role | Claude mapping |
|---|---|
| `fast reviewer` | `sonnet` |
| `fast fact-checker` | `sonnet` |
| `fast writer` | `sonnet` |
| `fast implementer` | `sonnet` |
| `deep reviewer` | `opus` |
| `deep maker` | `opus` |
| `external adversary` | Codex CLI via `codex-review-team` when available |
| `orchestrator` | `sonnet` unless a task explicitly requires deep judgment |

Concrete model names belong here and in Claude-native files only.

## Reproduction Contract

The following runtime paths must continue to work:

```text
~/.claude/CLAUDE.md
~/.claude/README.md
~/.claude/settings.json
~/.claude/keybindings.json
~/.claude/commands/
~/.claude/statusline.sh
~/.claude/track-toggle.sh
~/.claude/skills/
~/.claude/agents/
~/.claude/hooks/
~/.claude/tools/
~/.claude/utilities/
```

If a future split changes any target path, update `claude_setting/` first and
verify through the runtime path above.
