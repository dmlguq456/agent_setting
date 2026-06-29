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
| Skills | `adapters/claude/skills/` | `claude_setting/skills` |
| Agent modes | `adapters/claude/agent-modes/` | `claude_setting/agent-modes` |
| Hooks | `adapters/claude/hooks/` | `claude_setting/hooks` |
| Tools | `adapters/claude/tools/` | `claude_setting/tools` |
| Utilities | `adapters/claude/utilities/` | `claude_setting/utilities` |
| Loops | `adapters/claude/loops/` | `claude_setting/loops` |
| Scaffolds | `adapters/claude/scaffolds/` | `claude_setting/scaffolds` |
| Statusline | `adapters/claude/statusline.sh` | `claude_setting/statusline.sh` |
| `/track` implementation | `adapters/claude/track-toggle.sh` | `claude_setting/track-toggle.sh` |

`~/.claude/*` should point at `claude_setting/*`, not directly at common files.

## Worklog And Agent Notes Realization

Claude Code currently realizes the portable continuity layer through local paths:

| Portable name | Current Claude realization | Classification |
|---|---|---|
| `<agent-notes-root>` | `/home/nas/user/Uihyeop/notes/` | mutable continuity state |
| `<worklog-board-app>` | `/home/Uihyeop/.claude/worklog-board/` | external/local app workspace |
| `<worklog-board-app>-wt/` | `/home/Uihyeop/.claude/worklog-board-wt/` | app worktrees |

The Claude adapter preserves existing behavior: `autopilot-note` writes Layer 2
notes, triage proposals, digests, and feedback/change-review queue entries under
the notes root; the worklog-board app reads that state and owns UI approval
flows. The adapter must not move or delete existing data during harness
migration.

Keep these out of the harness repo: notes data, worklog local DB/cache, `.env*`,
`.next`, `node_modules`, `.dispatch`, app runtime logs, and worktrees. If the
board app source is later made portable, promote it as a separate app/tool with
its own repo or explicit source directory rather than treating the current
`~/.claude` workspace as adapter source.

## Design Harness Realization

Claude Code realizes the portable design harness through the projected
`claude_setting/tools/design-mcp` tree and Claude MCP registration:

```sh
claude mcp add design --scope user -- node ~/.claude/tools/design-mcp/server.js
cd ~/.claude/tools/design-mcp && npm run smoke
```

Portable capability specs refer to this as the runtime design harness. The
Claude adapter owns the concrete MCP command, `~/.claude/tools/design-mcp`
runtime path, and any Claude-specific preview/screenshot/console wiring.

## Compatibility Realizations

These surfaces are still consumed by Claude Code directly, but their runtime
paths now point at adapter-owned realization files instead of the common root:

| Surface | Current projection | Why compatibility realization is allowed for now | Required split |
|---|---|---|---|
| Skills | `claude_setting/skills -> ../adapters/claude/skills` | Adapter-owned concrete Claude Skill files preserve old behavior while portable specs grow under `capabilities/` | Continue splitting semantics into `capabilities/<name>.md`; keep Claude frontmatter and runtime wording here |
| Agent modes | `claude_setting/agent-modes -> ../adapters/claude/agent-modes` | Adapter-owned concrete mode projection files preserve current Claude behavior while `roles/MODES.md` classifies portability | Continue splitting adapter-coupled mode semantics into runtime-neutral fragments or adapter-native notes as non-Claude adapters implement equivalents |
| Hooks | `claude_setting/hooks -> ../adapters/claude/hooks` | Adapter-owned concrete hook projection files preserve current Claude behavior; `core/HOOKS.md` names the invariant layer | Continue splitting Claude payload handling from portable invariant checks as non-Claude adapters implement equivalents |
| Utilities | `claude_setting/utilities -> ../adapters/claude/utilities` | Adapter-owned concrete utility projection files preserve current Claude behavior while helper semantics remain shared | Move Claude-only helper behavior to adapter-native files when found; keep runtime-neutral contracts in the common utility docs or scripts |
| Tools | `claude_setting/tools -> ../adapters/claude/tools` | Adapter-owned concrete tool files preserve current Claude helper behavior while tool semantics are split | Isolate Claude session adapters under adapter or tool plugin |
| Loops | `claude_setting/loops -> ../adapters/claude/loops` | Adapter-owned concrete loop files preserve current Claude drill/oncall/study behavior | Split runtime-coupled loop invocation if non-Claude adapters need native loop runners |
| Scaffolds | `claude_setting/scaffolds -> ../adapters/claude/scaffolds` | Adapter-owned concrete scaffold files preserve current Claude design/template behavior | Move Claude-only scaffold assumptions into adapter-native files when found; keep portable scaffold intent in common docs |

Direct symlink passthrough from adapter-owned runtime surfaces back into the
common root is a temporary migration state, not the final adapter shape.

Agent files have completed the first split: portable role meaning is summarized
in `roles/README.md`, while Claude Agent frontmatter, tool lists, and concrete
model mapping live in `adapters/claude/agents/`.

Capability files have started the same split: portable capability meaning lives
in `capabilities/README.md` and `capabilities/<name>.md`, while Claude Skill
mechanics live as concrete adapter projection files under
`adapters/claude/skills/<name>/SKILL.md`. The current projection intentionally
preserves previous Claude behavior; future edits should move invariant meaning
to `capabilities/` first, then adjust the Claude Skill wording here.

Mode files now follow the same concrete projection pattern as skills:
`claude_setting/agent-modes` points at `adapters/claude/agent-modes/`, whose
family entries are adapter-owned files copied from the current `roles/modes/`
content. This preserves old Claude behavior while `roles/MODES.md` continues to
classify which fragments are portable, tool-contract-bound, or adapter-coupled.

Hook scripts now follow the same concrete projection pattern:
`claude_setting/hooks` points at `adapters/claude/hooks/`, whose files are
adapter-owned copies of the current shared `hooks/` scripts. This keeps the
existing Claude `settings.json` commands stable while `core/HOOKS.md` continues
to define the portable invariant layer and future adapter wrapper split.

Utility scripts now follow the same concrete projection pattern:
`claude_setting/utilities` points at `adapters/claude/utilities/`, whose files
are adapter-owned copies of the current shared `utilities/` scripts. This keeps
existing Claude hook/helper paths stable while future edits can split
runtime-neutral helper behavior from Claude-specific shell integration.

Scaffold assets now follow the same concrete projection pattern:
`claude_setting/scaffolds` points at `adapters/claude/scaffolds/`, whose files
are adapter-owned copies of the current shared `scaffolds/` assets. This keeps
Claude-facing scaffold paths stable while future edits can split portable
template intent from runtime-specific integration.

Loop helpers now follow the same concrete projection pattern:
`claude_setting/loops` points at `adapters/claude/loops/`, whose files are
adapter-owned copies of the current shared `loops/` helpers. This keeps current
Claude loop entry points available without treating the common root as the
runtime projection.

Tooling now follows the same concrete projection pattern:
`claude_setting/tools` points at `adapters/claude/tools/`, whose files are
adapter-owned copies of the current shared `tools/` helpers, excluding local
cache artifacts such as `__pycache__`. This keeps current Claude helper paths
available while future edits can split portable tool logic from runtime-specific
session integration.

The first-level Claude adapter support surfaces above no longer use symlink
passthrough entries back into the common root. `claude_setting/` remains the
runtime projection layer and should continue to point at `adapters/claude/*`.

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
