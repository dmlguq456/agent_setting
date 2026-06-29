# OpenCode Adaptation

This adapter maps the common agent harness onto OpenCode. It targets harness
parity on OpenCode, not Claude surface parity.

OpenCode has a richer native surface than an instruction-only runtime: it
ships native commands, skills, agents, MCP, and a JS/TS plugin hook system.
This adapter prefers those native surfaces first, then adds shell preflight
wrappers only for harness-specific signals that OpenCode does not expose
directly. Claude files are implementation references, not files to port
wholesale.

## Design Principle

Start from the portable invariant in `core/`, then map it onto OpenCode-native
features where they exist. Use OpenCode-native surfaces first for instructions,
commands, skills, agents, model/session/context management, approvals, MCP,
and plugin hooks. Add adapter wrappers only for harness-specific signals that
OpenCode does not provide directly.

Keep the workflow/capability meaning canonical, describe OpenCode artifact
layout and config surfaces as adapter data, prove the runtime discovers
adapter-owned artifacts before claiming support, and fail closed when a
runtime feature is undocumented or missing.

## Investigated OpenCode Native Surfaces

Investigated against OpenCode 1.17.x via the published config schema
(`https://opencode.ai/config.json`), the `opencode` CLI help output, the
`opencode debug` subcommands, and the built-in `customize-opencode` skill
documentation.

| OpenCode runtime surface | Native? | Adapter source / projection |
|---|---|---|
| Project config (`opencode.json` / `opencode.jsonc` / `.opencode/opencode.json`) | yes | user-owned; adapter documents the `instructions` entry that loads `AGENTS.md` |
| Global config (`~/.config/opencode/opencode.json`) | yes | user-owned; adapter documents projection entries |
| Instruction files (`instructions` array in config) | yes | `adapters/opencode/AGENTS.md` projected through `opencode_setting/AGENTS.md` |
| Commands (`.opencode/command/<name>.md` or `.opencode/commands/<name>.md`) | yes | not yet materialized; future adapter-owned output from `capabilities/` |
| Skills (`.opencode/skill/<name>/SKILL.md` or `.opencode/skills/<name>/SKILL.md`) | yes | not yet materialized; future adapter-owned output from `capabilities/` |
| External skill autoload (`~/.claude/skills/<name>/SKILL.md`, `~/.agents/skills/<name>/SKILL.md`) | yes (compat) | not relied on; adapter must generate its own skills, not depend on Claude skill autoload |
| Agents (`.opencode/agent/<name>.md` or `.opencode/agents/<name>.md`) | yes | not yet materialized; future adapter-owned output from `roles/` |
| Plugin hooks (JS/TS: `tool.execute.before`, `tool.execute.after`, `event`, `config`, `chat.message`, `command.execute.before`, `permission.ask`, `shell.env`, ...) | yes | not yet materialized; future adapter-owned plugin for harness guards |
| Permission model (`permission` config: `allow`/`ask`/`deny` per tool, per-agent override) | yes | adapter documents recommended permission rules; not a harness guard replacement |
| MCP servers (`mcp` config: local/remote) | yes | adapter documents design MCP registration when a visual harness is added |
| Model selection (`model`, `small_model`, per-agent `model`, `variant`) | yes | `adapters/opencode/bin/role-map.sh` resolves portable roles to model/variant |
| Statusline / footer | no user shell surface | TUI footer is native; harness status signals stay instruction-only/preflight |
| Shell hooks (Claude-style `settings.json` hook events) | no | harness guards run as explicit preflight wrappers |
| Session transcript | SQLite at `~/.local/share/opencode/opencode.db`, `opencode export <sid>` | distill source reader not yet implemented (tool-contract) |
| No-tools worker flag | not confirmed | `opencode run --agent <restricted-agent>` with deny permissions is a candidate but not yet verified; distill auto-apply stays disabled |

## Native Skill, Command, And Agent Surface Debt

OpenCode has native skill, command, and agent surfaces. This adapter does not
materialize them yet. Current support is instruction-first: load `AGENTS.md`,
read `capabilities/`, and run `preflight.sh capability-info`. That is the safe
default while the projection boundary is being fixed.

Before adding OpenCode-native skills, commands, or agents:

1. Use `capabilities/<name>.md` and `roles/` as source, not
   `skills/<name>/SKILL.md` or `adapters/claude/skills/`.
2. Generate or maintain concrete adapter-owned output under an explicit
   OpenCode adapter path, for example `adapters/opencode/skills/<name>/SKILL.md`,
   `adapters/opencode/command/<name>.md`, or `adapters/opencode/agent/<name>.md`.
3. Keep OpenCode frontmatter (`name`, `description`, `mode`, `model`,
   `permission`, `variant`), invocation syntax, and permission assumptions in
   the OpenCode adapter.
4. Add a guard that proves every generated OpenCode skill/command/agent maps
   to a portable capability or role and that no Claude-native file is exposed
   as OpenCode-native.
5. Verify discoverability using the OpenCode runtime contract (`opencode debug
   skill`, `opencode debug agent`, or TUI invocation), not byte parity with
   Claude files. Use `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` during this check
   so OpenCode's `~/.claude/skills/` compatibility autoload cannot produce a
   false pass.

Until that exists, OpenCode capability support remains wrapper/instruction
based. Design capabilities are a tool-contract exception: OpenCode must
provide or map an adapter visual harness before claiming full support, and
`capability-info` reports `status=tool-contract` for those entries.

## Native Plugin Hook Surface Debt

OpenCode exposes JS/TS plugin hooks that could enforce harness guards
(`tool.execute.before` for artifact order, git state, memory write). This
adapter does not materialize a plugin yet. Current support runs the same
shell preflight wrappers as the Codex adapter, called explicitly by the agent
or by `AGENTS.md` instructions.

Before adding an OpenCode plugin for harness guards:

1. Implement the plugin in TypeScript under `adapters/opencode/plugin/` or as
   a configured `plugin:` entry.
2. Bridge `tool.execute.before` to the shared shell guards
   (`hooks/artifact-guard.sh`, `hooks/git-state-guard.sh`,
   `hooks/builtin-memory-guard.sh`) via a small shell invocation from the
   plugin.
3. Prove the plugin is discovered by OpenCode (`opencode debug config` or a
   TUI startup check).
4. Keep the shell preflight wrappers as the fallback path so the adapter
   remains usable without the plugin.

Until the plugin exists, harness guards are instruction-only preflight.

## Explicit Non-Support

OpenCode must not consume these Claude-native files as native configuration:

| Claude-native surface | OpenCode status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; OpenCode uses `opencode.json` config + plugin hooks |
| `adapters/claude/commands/` | Not consumable; OpenCode commands must be expressed as `.opencode/command/<name>.md` or `command:` config entries |
| `skills/*/SKILL.md` | Compatibility reference only; OpenCode should start from `capabilities/README.md`. The `~/.claude/skills/` autoload path is a compat convenience, not an adapter projection. |
| `adapters/claude/statusline.sh` | Not consumable; OpenCode has no user shell statusline surface |
| `adapters/claude/track-toggle.sh` | Semantics reusable, implementation depends on Claude session id fallback |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; OpenCode should start from `roles/README.md`. Claude Agent frontmatter is not OpenCode agent frontmatter. |
| `adapters/claude/hooks/*.sh` | Reference only; OpenCode has no shell hook event schema. Guards run as explicit preflight. |
| `roles/modes/design/*` | Compatibility reference only until OpenCode has an equivalent visual/browser verification harness |

## Status Surface Boundary

OpenCode has a native TUI footer that shows model, context, tokens, and
session state. There is no user-customizable shell statusline script
(`statusline.sh` equivalent) in the OpenCode config schema. Do not attempt to
replace the native footer, and do not project `adapters/claude/statusline.sh`.

Harness-specific status signals need OpenCode-native realization:

| Harness signal | OpenCode direction |
|---|---|
| tracked/untracked workflow state | explicit `preflight.sh mode` until a native prompt/session surface or plugin exists |
| tracked/untracked workflow toggle | explicit `preflight.sh track`; do not expose Claude `/track` command files |
| artifact root detection | `preflight.sh write` and shared artifact-root helper |
| headless/autopilot/background jobs | `opencode run` headless mode exists; full autopilot dispatch redesign against OpenCode session/agent model before adding UI |
| sibling `-wt/<slug>` dispatch detection | preserve the worktree naming invariant; choose an OpenCode-native display surface later |
| pipeline stage nudges | preflight/AGENTS instructions first; UI only when OpenCode exposes a suitable surface |
| oncall/note/study/drill loop nudges | `preflight.sh briefing` / future loop-specific wrappers |
| merge/rebase/merged-branch risk | `preflight.sh write` git safety checks plus any future OpenCode-native warning surface |

## Required OpenCode Mappings

| Portable invariant | OpenCode adaptation requirement |
|---|---|
| artifact order | Run `adapters/opencode/bin/preflight.sh write <file> [session-id]` before writes |
| git state safety | Run `adapters/opencode/bin/preflight.sh write <file> [session-id]` before edits |
| memory write guard | Run `adapters/opencode/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | Run `adapters/opencode/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | Run `adapters/opencode/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/opencode/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| workflow start cleanup | Run `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` when no automatic session-start hook is attached |
| workflow signal | Run `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]` as explicit prompt/session reminder; no statusline assumption |
| workflow toggle | Run `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly requests tracked/untracked mode switching |
| memory inject | Run `adapters/opencode/bin/preflight.sh memory [cwd]` for plain-text session-start memory injection |
| memory recall | Run `adapters/opencode/bin/preflight.sh recall <prompt> [cwd]` before prompt handling when no automatic prompt hook is attached |
| oncall briefing | Run `adapters/opencode/bin/preflight.sh briefing [cwd]` before prompt handling on the dedicated agent desk |
| memory distill | Transcript delta extraction requires an OpenCode session source reader (SQLite or `opencode export`) that is not yet implemented in the shared memory CLI; automatic memory mutation remains disabled until an OpenCode no-tools worker contract is verified |
| worklog state signal | Run `adapters/opencode/bin/preflight.sh worklog [cwd]` to inspect configured `<agent-notes-root>` / `<worklog-board-app>` paths read-only before OpenCode updates notes or diagnoses board state |
| role profiles | Read `roles/README.md`, then run `adapters/opencode/bin/preflight.sh role <portable-role>` to resolve OpenCode model/variant settings |
| role modes | Read `roles/MODES.md`, then run `adapters/opencode/bin/preflight.sh mode-info <family/mode>`; treat adapter-coupled modes as unsupported unless wrappers exist |
| hook invariants | Read `core/HOOKS.md`; run explicit preflight wrappers until an OpenCode plugin hook realization exists |
| capabilities | Read `capabilities/README.md`, then run `adapters/opencode/bin/preflight.sh capability-info <capability>`; do not assume Claude Skill invocation |

## Model Mapping

OpenCode should expose concrete choices through environment or config:

```text
AGENT_MODEL_FAST
AGENT_MODEL_DEEP
AGENT_MODEL_EXTERNAL
AGENT_VARIANT_FAST
AGENT_VARIANT_DEEP
AGENT_MODEL_ORCHESTRATOR
AGENT_EXTERNAL_CMD
```

OpenCode uses `provider/model-id` model strings and a `variant` field on
agents for reasoning profile selection. There is no numeric reasoning-effort
config field; the adapter maps portable reasoning intent to `variant` and
agent selection.

Until those are implemented, OpenCode uses the portable role names and reports
any unavailable role explicitly.

## Current Projection Boundary

`opencode_setting/` should remain minimal until adapted surfaces exist. It may
expose `AGENTS.md`, `README.md`, `core/`, `capabilities/`, `bin/`, selected
tools, and selected utilities, but must not expose Claude-native
`settings.json`, `commands/`, `skills/`, `statusline.sh`, or `hooks/` as if
OpenCode could consume them.

`opencode_setting/tools` points at `adapters/opencode/tools/`, not the entire
shared `tools/` directory. The current allowlist is:

- `memory/mem.py` (OpenCode-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (OpenCode-owned launcher for recall)

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `design-mcp` or
`web-bundle` until OpenCode has a documented design/tooling realization that
uses them directly.

`opencode_setting/utilities` points at `adapters/opencode/utilities/`, not the
entire shared `utilities/` directory. The current allowlist is:

- `agent-home.sh` (OpenCode-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Do not project `dispatch-liveness.sh` until OpenCode has a documented
transcript liveness surface equivalent to Claude session transcript mtimes. Do
not project material/design helpers such as `extract_web_figures.py` until an
OpenCode capability uses them directly.

## Distillation Boundary

Claude's adapter can run a detached `claude -p` worker with tool use denied by
runtime flags. OpenCode has `opencode run` for headless execution and a
per-agent permission model, but no explicit confirmed equivalent to a no-tools
worker flag. The OpenCode adapter therefore separates the pipeline and keeps
it disabled by default:

1. `distill-delta` is a tool-contract: the shared memory CLI does not yet have
   an OpenCode session source reader. An `OpenCodeDbSource` or
   `OpenCodeExportSource` implementing the `.messages()` interface
   (`Msg(role, ts, text, uuid, is_sidechain)`) is required before delta
   extraction works.
2. `distill-propose` is disabled by default. Even after a source reader exists,
   it must not auto-apply memory mutations until an OpenCode no-tools worker
   contract is verified (candidate: `opencode run --agent <restricted-agent>`
   with deny permissions, or a future plugin-mediated worker).
3. The proposal, when implemented, would be parsed by the shared
   `tools/memory/apply-distill-actions.py` applier only when
   `OPENCODE_DISTILL_APPLY=1` is explicitly set.
4. Automatic distillation stays disabled until both a source reader and a
   no-tools worker contract are proven.

## Worklog Boundary

OpenCode must treat `<agent-notes-root>` as mutable continuity state, not as
harness source. Before changing notes/routing state, run normal `write`
preflight for the target file and inspect `preflight.sh worklog` output.
OpenCode may read/write notes-root files only when the task is explicitly about
notes, triage, feedback, or worklog routing. It must not copy worklog-board
DBs, caches, `.env*`, build output, dispatch logs, or worktrees into this repo.
