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
| Commands (`.opencode/command/<name>.md` or `.opencode/commands/<name>.md`) | yes | `adapters/opencode/commands/<name>.md` generated from `capabilities/` |
| Skills (`.opencode/skill/<name>/SKILL.md` or `.opencode/skills/<name>/SKILL.md`) | yes | `adapters/opencode/skills/<name>/SKILL.md` generated from `capabilities/` |
| External skill autoload (`~/.claude/skills/<name>/SKILL.md`, `~/.agents/skills/<name>/SKILL.md`) | yes (compat) | not relied on; adapter must generate its own skills, not depend on Claude skill autoload |
| Agents (`.opencode/agent/<name>.md` or `.opencode/agents/<name>.md`) | yes | `adapters/opencode/agents/<name>/<name>.md` generated from `roles/README.md` with `mode: subagent` |
| Plugin hooks (JS/TS: `tool.execute.before`, `tool.execute.after`, `event`, `config`, `chat.message`, `command.execute.before`, `permission.ask`, `shell.env`, ...) | yes | `adapters/opencode/plugins/agent-harness-guards.js` bridges write/edit/patch tool execution to shared guard preflight |
| Permission model (`permission` config: `allow`/`ask`/`deny` per tool, per-agent override) | yes | adapter documents recommended permission rules; not a harness guard replacement |
| Permission contract wrapper | yes | `adapters/opencode/bin/preflight.sh permissions` reports native permission surfaces and rejects Claude `allowedTools` as a portable contract |
| MCP servers (`mcp` config: local/remote) | yes | `adapters/opencode/bin/preflight.sh mcp` reports native MCP surfaces and rejects Claude `settings.json` MCP payloads as a portable contract |
| Model selection (`model`, `small_model`, per-agent `model`, `variant`) | yes | `adapters/opencode/bin/role-map.sh` resolves portable roles to model/variant |
| Statusline / footer | no user shell surface | TUI footer is native; harness status signals stay instruction-only/preflight |
| Shell hooks (Claude-style `settings.json` hook events) | no | harness guards run as explicit preflight wrappers |
| Session transcript | SQLite at `~/.local/share/opencode/opencode.db`, `opencode export <sid>` | `distill-delta` uses the shared OpenCode export source reader |
| No-tools worker flag | not confirmed | `opencode run --agent <restricted-agent>` with deny permissions is a candidate but not yet verified; distill auto-apply stays disabled |

## Native Skill, Command, And Agent Surface Debt

OpenCode has native skill, command, and agent surfaces. This adapter now
materializes native Skills from `capabilities/*.md` and native Agents from
`roles/README.md`, plus native Commands from `capabilities/*.md`. Current
support still runs through explicit preflight wrappers for guard and
tool-contract reporting.

Before adding or changing OpenCode-native skills, commands, or agents:

1. Use `capabilities/<name>.md` and `roles/` as source, not
   `skills/<name>/SKILL.md` or `adapters/claude/skills/`.
2. Generate or maintain concrete adapter-owned output under an explicit
   OpenCode adapter path, for example `adapters/opencode/skills/<name>/SKILL.md`,
   `adapters/opencode/commands/<name>.md`, or `adapters/opencode/agents/<name>/<name>.md`.
3. Keep OpenCode frontmatter (`name`, `description`, `mode`, `model`,
   `permission`, `variant`), command argument passthrough (`$ARGUMENTS`), and
   permission assumptions in the OpenCode adapter.
4. Add a guard that proves every generated OpenCode skill/command/agent maps
   to a portable capability or role and that no Claude-native file is exposed
   as OpenCode-native.
5. Verify discoverability using the OpenCode runtime contract (`opencode debug
   skill`, `opencode debug agent`, or TUI invocation), not byte parity with
   Claude files. Use `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` during this check
   so OpenCode's `~/.claude/skills/` compatibility autoload cannot produce a
   false pass.

Design capabilities are a tool-contract exception: OpenCode has native Skill
guidance for them, but must run the adapter visual harness before claiming full
support. `capability-info` reports `status=tool-contract` for those entries.

`roles/modes/material/browser-fetch.md` has an OpenCode-owned executable
tool-contract surface:
`adapters/opencode/bin/preflight.sh browser-fetch --check <url>` verifies
rendered browser access through `adapters/opencode/tools/material/` and reports
exit 69 when the local Playwright browser stack is unavailable.

`roles/modes/material/data-script.md` is the first material mode with an
OpenCode-owned executable tool-contract surface:
`adapters/opencode/bin/preflight.sh data-script --check <script.py>` verifies
generated Python analysis scripts through `adapters/opencode/tools/material/`.

`roles/modes/material/figure-gen.md` has an OpenCode-owned executable
tool-contract surface:
`adapters/opencode/bin/preflight.sh figure-gen --check <script.py>` verifies
generated matplotlib/seaborn figure scripts through
`adapters/opencode/tools/material/`.

`roles/modes/material/pdf-extract.md` has an OpenCode-owned executable
tool-contract surface:
`adapters/opencode/bin/preflight.sh pdf-extract --check <file.pdf>` verifies
local PDF text extraction through `adapters/opencode/tools/material/` and
reports exit 69 when the local extractor is unavailable.

`roles/modes/material/web-image-search.md` has an OpenCode-owned executable
tool-contract surface:
`adapters/opencode/bin/preflight.sh web-image-search --check <query>` verifies
a configured image-search provider command through
`adapters/opencode/tools/material/` and reports exit 69 when no provider is
configured.

`roles/modes/qa/security-review.md` is portable read-only mode guidance for
OpenCode. It is consumed with OpenCode file and git diff tools and does not
project or invoke Claude's `/security-review` slash command.

`roles/modes/research/claim-verify.md` has an OpenCode-owned executable
tool-contract surface:
`adapters/opencode/bin/preflight.sh claim-verify --check <claim>` verifies a
configured external verification provider command through
`adapters/opencode/tools/research/` and reports exit 69 when no provider is
configured.

`roles/modes/qa/test.md` has an OpenCode-owned executable tool-contract
surface:
`adapters/opencode/bin/preflight.sh verification-runner --check -- <command>`
checks explicit verification commands and the same wrapper can execute them
with a bounded timeout.

## Native Plugin Hook Surface

OpenCode exposes JS/TS plugin hooks that can enforce part of the harness guard
contract. This adapter materializes a concrete OpenCode plugin at
`adapters/opencode/plugins/agent-harness-guards.js`. It uses `chat.message` plus
`experimental.chat.system.transform` to inject prompt-time workflow, memory,
recall, and briefing context through `adapters/opencode/bin/preflight.sh`
without copying Claude hook JSON. It uses `tool.execute.before` to detect
write/edit/patch targets and calls `adapters/opencode/bin/preflight.sh write
<file> <session-id>`, which runs the portable artifact-order, git-state, and
memory-write guards. It also uses `tool.execute.after` to route saved design
HTML files through `adapters/opencode/bin/preflight.sh design <file>` as a
post-write console-check alert path.

When changing the plugin:

1. Keep it under `adapters/opencode/plugins/` as adapter-owned JS/TS.
2. Bridge to `adapters/opencode/bin/preflight.sh`, not to Claude hook files.
3. Prove discovery with `opencode debug config`.
4. Keep shell preflight wrappers as fallback so the adapter remains usable
   when plugins are disabled.

The plugin covers prompt lifecycle context, write guard enforcement, and design
post-write console checks. Distillation still uses explicit preflight wrappers
until the OpenCode no-tools worker contract is verified.

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
| workflow/artifact/notes/git-risk snapshot | explicit `preflight.sh status`; keep OpenCode native UI/config for model/context/session fields |
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
| workflow start cleanup | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh start [cwd] [session-id]` once per session; run it manually when plugins are unavailable |
| workflow signal | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh mode [cwd] [session-id]`; no statusline assumption |
| workflow toggle | Run `adapters/opencode/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly requests tracked/untracked mode switching |
| memory inject | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh memory [cwd]` once per session; run it manually when plugins are unavailable |
| memory recall | OpenCode plugin `chat.message` captures prompt text and system transform runs `adapters/opencode/bin/preflight.sh recall <prompt> [cwd]`; run it manually when plugins are unavailable |
| oncall briefing | OpenCode plugin system transform runs `adapters/opencode/bin/preflight.sh briefing [cwd]`; run it manually when plugins are unavailable |
| memory distill | Transcript delta extraction uses `opencode export` through the shared memory CLI; automatic memory mutation remains disabled until an OpenCode no-tools worker contract is verified |
| worklog state signal | Run `adapters/opencode/bin/preflight.sh worklog [cwd]` to inspect configured `<agent-notes-root>` / `<worklog-board-app>` paths read-only before OpenCode updates notes or diagnoses board state |
| role profiles | Read `roles/README.md`, then run `adapters/opencode/bin/preflight.sh role <portable-role>` to resolve OpenCode model/variant settings |
| permission mapping | Run `adapters/opencode/bin/preflight.sh permissions` to inspect the OpenCode native permission contract and confirm Claude `allowedTools` is unsupported |
| MCP mapping | Run `adapters/opencode/bin/preflight.sh mcp --check` to inspect OpenCode's native MCP CLI/config surface; do not copy Claude `settings.json` MCP registrations or project `tools/design-mcp` wholesale |
| headless dispatch | Run `adapters/opencode/bin/preflight.sh headless --check <worktree>` before OpenCode `run` dispatch; it checks the worktree and command availability without launching. While waiting on dispatched work, run `adapters/opencode/bin/preflight.sh liveness [jobs.log]` to match open jobs to OpenCode SQLite sessions by `session.directory` and latest session/message/part update time |
| role modes | Read `roles/MODES.md`, then run `adapters/opencode/bin/preflight.sh mode-info <family/mode>`; treat adapter-coupled modes as unsupported unless wrappers exist, obey `fallback=reference-only`, and satisfy any named `tool_contract` / `tool_contract_check` before claiming tool-contract modes |
| hook invariants | Read `core/HOOKS.md`; OpenCode plugin hooks cover prompt lifecycle context, write/edit/patch guards, and design HTML post-write checks, while explicit preflight wrappers remain fallback for disabled/untrusted plugins and events not yet covered |
| capabilities | Read `capabilities/README.md`, then run `adapters/opencode/bin/preflight.sh capability-info <capability>`; do not assume Claude Skill invocation |

## Model Mapping

OpenCode exposes concrete choices through environment or config and resolves
them with `adapters/opencode/bin/preflight.sh role <portable-role>`:

```text
AGENT_MODEL_FAST
AGENT_MODEL_DEEP
AGENT_MODEL_EXTERNAL
AGENT_VARIANT_FAST
AGENT_VARIANT_DEEP
AGENT_VARIANT_EXTERNAL
AGENT_MODEL_ORCHESTRATOR
AGENT_VARIANT_ORCHESTRATOR
AGENT_EXTERNAL_CMD
```

OpenCode uses `provider/model-id` model strings and a `variant` field on
agents for reasoning profile selection. There is no numeric reasoning-effort
config field; the adapter maps portable reasoning intent to `variant` and
agent selection.

When no concrete model is configured, the adapter reports `opencode-default`
and `runtime-default`. `external adversary` remains unavailable unless
`AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured.

## Current Projection Boundary

`opencode_setting/` should remain minimal and explicit. It may expose
`AGENTS.md`, `README.md`, `core/`, `capabilities/`, `roles/`, `bin/`,
`opencode-skills`, `opencode-agents`, `opencode-commands`, `opencode-plugins`,
selected tools, and selected utilities, but must not expose Claude-native
`settings.json`, `commands/`, `skills/`, `statusline.sh`, or `hooks/` as if
OpenCode could consume them.

`opencode_setting/tools` points at `adapters/opencode/tools/`, not the entire
shared `tools/` directory. The current allowlist is:

- `memory/mem.py` (OpenCode-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (OpenCode-owned launcher for recall)
- `material/browser-fetch.sh` (OpenCode-owned launcher for rendered web page extraction)
- `material/data-script.sh` (OpenCode-owned launcher for Python data-analysis scripts)
- `material/figure-gen.sh` (OpenCode-owned launcher for generated matplotlib figure scripts)
- `material/pdf-extract.sh` (OpenCode-owned launcher for local PDF text extraction)
- `material/web-image-search.sh` (OpenCode-owned launcher for configured image search providers)
- `qa/verification-runner.sh` (OpenCode-owned launcher for explicit verification commands)
- `research/claim-verify.sh` (OpenCode-owned launcher for configured external claim verification providers)
- `design/visual-harness.sh` (OpenCode-owned launcher for render/screenshot/console checks)

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `web-bundle` until
OpenCode has a documented design/tooling realization that uses it directly. The
shared `design-mcp` package is not projected wholesale; OpenCode exposes only
the adapter-owned visual harness launcher.

`opencode_setting/utilities` points at `adapters/opencode/utilities/`, not the
entire shared `utilities/` directory. The current allowlist is:

- `agent-home.sh` (OpenCode-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `harness-status.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Do not project the shared `dispatch-liveness.sh`; it assumes Claude
`projects/<encoded-cwd>/*.jsonl`. OpenCode uses the adapter-owned
`adapters/opencode/bin/dispatch-liveness.py`, exposed as
`adapters/opencode/bin/preflight.sh liveness [jobs.log]`, and maps open
dispatch jobs to `~/.local/share/opencode/opencode.db` sessions by
`session.directory`. Do not project material/design helpers such as
`extract_web_figures.py` until an OpenCode capability uses them directly.

## Distillation Boundary

Claude's adapter can run a detached `claude -p` worker with tool use denied by
runtime flags. OpenCode has `opencode run` for headless execution and a
per-agent permission model, but no explicit confirmed equivalent to a no-tools
worker flag. The OpenCode adapter therefore separates the pipeline and keeps
it disabled by default:

1. `distill-delta` is supported through the shared memory CLI's
   `OpenCodeExportSource`, which normalizes `opencode export <session-id>` JSON
   into the `.messages()` interface (`Msg(role, ts, text, uuid, is_sidechain)`).
2. `distill-propose` is disabled by default. It must not auto-apply memory
   mutations until an OpenCode no-tools worker
   contract is verified (candidate: `opencode run --agent <restricted-agent>`
   with deny permissions, or a future plugin-mediated worker).
3. The proposal, when implemented, would be parsed by the shared
   `tools/memory/apply-distill-actions.py` applier only when
   `OPENCODE_DISTILL_APPLY=1` is explicitly set.
4. Automatic distillation stays disabled until a no-tools worker contract is
   proven.

## Worklog Boundary

OpenCode must treat `<agent-notes-root>` as mutable continuity state, not as
harness source. Before changing notes/routing state, run normal `write`
preflight for the target file and inspect `preflight.sh worklog` output.
OpenCode may read/write notes-root files only when the task is explicitly about
notes, triage, feedback, or worklog routing. It must not copy worklog-board
DBs, caches, `.env*`, build output, dispatch logs, or worktrees into this repo.
