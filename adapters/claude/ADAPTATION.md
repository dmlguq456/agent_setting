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
| Runtime worker wrappers | `adapters/claude/bin/` | `claude_setting/bin` |
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
| Workflow toggle helper | `adapters/claude/utilities/workflow-toggle.sh` | `claude_setting/utilities/workflow-toggle.sh` |

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

## Memory Distiller Realization

Claude Code realizes the portable memory distillation hooks through
`adapters/claude/settings.json` hook registration and concrete hook scripts under
`adapters/claude/hooks/`.

The current Claude distiller mapping is:

| Portable worker role | Claude realization |
|---|---|
| `fast distiller` / turn-counter add-only worker | `adapters/claude/bin/mem-distill-worker.sh` maps `fast-distiller` to detached `claude -p` default `claude-sonnet-4-6` |
| `deep curator` / SessionEnd action worker | `adapters/claude/bin/mem-distill-worker.sh` maps `deep-curator` to detached `claude -p` default `claude-opus-4-8` |

`hooks/mem-distill-dispatch.sh` keeps the existing Claude behavior: opt-in via
`MEM_DISTILL_ENABLE=1`, recursion guard through `MEM_DISTILL=1`, no-tools output
contract through the Claude worker's `--disallowedTools`, JSON/action validation
in shell/Python code, and `mem` CLI as the only DB mutation path. The shared
dispatcher contract is `MEM_DISTILL_WORKER=<executable>` with
`<mode> <model> <prompt-file>` arguments; this adapter sets that executable to
the Claude worker when using the shared dispatcher. Other adapters must provide
their own transcript source and worker invocation or explicitly keep automatic
distillation unsupported.

## Dispatch And Statusline Realization

Claude Code realizes the portable dispatch contract through headless Claude Code
main sessions and the adapter-owned statusline script. Its CLI supports one-off
model/effort overrides, so dispatch model selection follows the core rule:
main/orchestrator chooses per job and the wrapper only reflects that choice:

- Full ceremony dispatch runs a background headless main in the target worktree,
  currently shaped as `claude -p "/autopilot-code --mode <mode> --qa <level> ..."`
  with tools pre-approved through Claude Code flags/settings.
- The headless wrapper does not choose a default model. The main/orchestrator
  selects `--model-role <portable-role>`, `--model <model> --effort <level>`,
  or explicit `--inherit-model-settings` per job; that is where simple jobs
  are downshifted and complex jobs are escalated.
- Dispatch prompts must spell out capability, mode, and QA options because
  `adapters/claude/statusline.sh` derives the `>_ running` display from process
  command lines and sibling `-wt/<slug>` worktree paths.
- `utilities/dispatch-liveness.sh` inspects Claude session transcript mtimes
  under the Claude runtime project log layout to catch hung headless jobs.

Codex and future adapters should preserve the dispatch invariant, but must map
it onto their own thread/subagent/session/status surfaces instead of copying the
Claude statusline or `claude -p` process model.

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
`adapters/claude/track-toggle.sh` is now only the Claude `/track` wrapper; the
portable tracked/untracked flag semantics live in
`adapters/claude/utilities/workflow-toggle.sh`, matching the common
`utilities/workflow-toggle.sh` helper.

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

## Role Profile Frontmatter Mapping

Claude Agent frontmatter `model:` values are adapter-specific runtime hints.
They preserve the pre-migration behavior for the portable role families defined
in `core/CONVENTIONS.md §2`.

| Agent | Portable role | Claude frontmatter | Runtime behavior |
|---|---|---|---|
| `기획팀` (plan-team) | deep maker | `opus` | deep maker 단일 |
| `품질관리팀` (qa-team) | variable reviewer | `opus` | Review modes select fast/deep reviewer combinations by QA level; test/security modes use their own reviewer split |
| `연구팀` (research-team) | variable research reviewer | `opus` | Default deep maker/reviewer; fact-checker and light QA subroles use fast reviewer/fact-checker |
| `자료팀` (material-team) | deep maker default, fast tool worker subroles | `opus` | Collection/extraction subroles may use fast tool worker; figure/data synthesis stays deep maker |
| `개발팀` (dev-team) | fast implementer default | `sonnet` | Default implementation worker; complex API/library design can be escalated to deep maker |
| `디자인팀` (design-team) | deep maker with fast verifier | `opus` | Maker uses deep maker; critic/verifier split by nuance and mechanicality |
| `편집팀` (editorial-team) | deep maker/editor with fast reviewer subrole | `opus` | Translate/polish uses deep editor; review uses fast reviewer |
| `codex-review-team` | external adversary orchestrator | `sonnet` | Wrapper invokes Codex CLI external review and summarizes the result; the wrapper is not the actual reviewer |

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
