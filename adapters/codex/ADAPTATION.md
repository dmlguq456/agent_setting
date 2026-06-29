# Codex Adaptation

This adapter is not yet behavior-equivalent to the Claude Code adapter.
It defines the required mapping so Codex support can be built without copying
Claude-specific assumptions into the common core.

## Design Principle

Codex adaptation targets harness parity on Codex, not Claude surface parity.
Start from the portable invariant in `core/`, then map it onto Codex-native
features where they exist. Claude files are implementation references, not files
to port wholesale.

Use Codex-native surfaces first for model/session/context/status, approvals,
sandboxing, skills/plugins, and built-in slash commands. Add adapter wrappers
only for harness-specific signals that Codex does not provide directly.

## External Reference Lessons

GSD Core (`https://github.com/open-gsd/gsd-core`) is a useful cross-runtime
installer reference pattern, not a source to copy. The relevant lesson is the
seam:

- keep the workflow/capability meaning canonical;
- describe each runtime's artifact layout and config surface as data;
- convert canonical files into runtime-native artifacts;
- prove the runtime discovers those artifacts;
- fail closed when a runtime feature is undocumented or missing.

For this adapter, that means Codex support should not be measured by whether
Claude files are visible under `codex_setting/`. It should be measured by
whether Codex has a native entrypoint or an explicit wrapper for the portable
invariant.

## Native Codex Surfaces

| Codex runtime surface | Adapter source | Projection |
|---|---|---|
| Session bootstrap | `adapters/codex/AGENTS.md` | `codex_setting/AGENTS.md` |
| Adapter guide | `adapters/codex/README.md` | `codex_setting/README.md` |
| Common contract | `core/` | `codex_setting/core` |
| Capability catalog | `capabilities/` | `codex_setting/capabilities` |
| Role catalog | `roles/` | `codex_setting/roles` |
| Preflight wrappers | `adapters/codex/bin/` | `codex_setting/bin` |
| Skills | `adapters/codex/skills/<name>/SKILL.md` generated from `capabilities/` | `codex_setting/codex-skills` |
| Plugin marketplace | `adapters/codex/.agents/plugins/marketplace.json` plus `adapters/codex/plugins/agent-harness-codex` | `codex_setting/codex-plugin-marketplace` |
| Shared helper tools | selected `tools/`, selected `utilities/` | `codex_setting/tools`, `codex_setting/utilities` |
| Selected tools | `adapters/codex/tools/` adapter launchers plus selected portable tool projections | `codex_setting/tools` |
| Selected utilities | `adapters/codex/utilities/` adapter wrappers plus selected portable utility projections | `codex_setting/utilities` |

## Native Skill And Plugin Surface

Current Codex support includes generated native Skill projections:
`adapters/codex/skills/<name>/SKILL.md` is generated from
`capabilities/<name>.md` by `adapters/codex/bin/sync-native-skills.py` and
projected as `codex_setting/codex-skills`.

The same generated skills are also packaged into the adapter-owned Codex plugin
`adapters/codex/plugins/agent-harness-codex`, with repo-local marketplace
metadata under `adapters/codex/.agents/plugins/marketplace.json`. This makes
the harness discoverable through Codex's native plugin installer without
exposing Claude Skill files.

Codex custom prompts are deprecated. Command-like harness entries are therefore
realized through native Skills and the installable plugin, not through
`prompts/` files or Claude slash-command projections.

Before adding or changing Codex-native skills or plugins:

1. Use `capabilities/<name>.md` and `roles/` as source, not
   `skills/<name>/SKILL.md` or `adapters/claude/skills/`.
2. Generate or maintain concrete adapter-owned output under an explicit Codex
   adapter path, for example `adapters/codex/skills/<name>/SKILL.md`.
3. Keep Codex frontmatter, invocation syntax, sandbox/approval assumptions, and
   plugin metadata in the Codex adapter.
4. Add a guard that proves every generated Codex skill maps to a portable
   capability and that no Claude-native Skill file is exposed as Codex-native.
5. Verify discoverability using the Codex runtime contract, not byte parity with
   Claude files.

Design capabilities are a tool-contract exception: Codex has native Skill
guidance for them, but must provide or map an adapter visual harness before
claiming full support. `capability-info` reports `status=tool-contract` for
those entries.

The boundary guard checks that generated Codex skills and the generated Codex
plugin remain in sync, and that neither surface is built from Claude Skill
files.

## Explicit Non-Support

Codex must not consume these Claude-native files as native configuration:

| Claude-native surface | Codex status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; Codex needs wrapper/preflight equivalents |
| `adapters/claude/commands/` | Not consumable; Codex commands must be expressed as AGENTS instructions or wrapper commands |
| `skills/*/SKILL.md` | Compatibility reference only; Codex should start from `capabilities/README.md` |
| `adapters/claude/statusline.sh` | Not consumable; input schema is Claude statusline JSON |
| `adapters/claude/track-toggle.sh` | Do not consume; portable semantics live in `utilities/workflow-toggle.sh`, and Codex exposes them through `preflight.sh track` |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; Codex should start from `roles/README.md` |
| `roles/modes/design/*` | Compatibility reference only until Codex has an equivalent visual/browser verification harness |

## Status Surface Boundary

Codex has its own `/statusline` configuration for the TUI footer. Do not replace
it with `adapters/claude/statusline.sh`, and do not duplicate Codex-native footer
items such as model, context, token/usage/limits, git baseline, session, or
Codex fast-mode state.

Harness-specific status signals still need Codex-native realization:

| Harness signal | Codex direction |
|---|---|
| stale workflow bypass flag cleanup | explicit `preflight.sh start` until a native session-start surface exists |
| tracked/untracked workflow state | explicit `preflight.sh mode` until a native prompt/session surface exists |
| tracked/untracked toggle | explicit `preflight.sh track`; do not expose Claude `/track` command files |
| artifact root detection | `preflight.sh write` and shared artifact-root helper |
| headless/autopilot/background jobs | redesign against Codex thread/subagent/session model before adding UI |
| sibling `-wt/<slug>` dispatch detection | preserve the worktree naming invariant; choose a Codex-native display surface later |
| pipeline stage nudges | preflight/AGENTS instructions first; UI only when Codex exposes a suitable surface |
| oncall/note/study/drill loop nudges | `preflight.sh briefing` / future loop-specific wrappers |
| merge/rebase/merged-branch risk | `preflight.sh write` git safety checks plus any future Codex-native warning surface |

## Required Codex Mappings

| Portable invariant | Codex adaptation requirement |
|---|---|
| artifact order | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| git state safety | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits |
| memory write guard | Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before writes |
| design post-write verification | Run `adapters/codex/bin/preflight.sh design <file>` after design HTML writes |
| spec read gate | Run `adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual reads and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]` before spec/code capabilities |
| workflow start cleanup | Run `adapters/codex/bin/preflight.sh start [cwd] [session-id]` at session start when no automatic hook is attached |
| workflow signal | Run `adapters/codex/bin/preflight.sh mode [cwd] [session-id]` as explicit prompt/session reminder; no statusline assumption |
| workflow toggle | Run `adapters/codex/bin/preflight.sh track [cwd] [session-id]` only when the user explicitly requests tracked/untracked mode switching |
| memory inject | Run `adapters/codex/bin/preflight.sh memory [cwd]` for plain-text session-start memory injection |
| memory recall | Run `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` before prompt handling when no automatic prompt hook is attached |
| oncall briefing | Run `adapters/codex/bin/preflight.sh briefing [cwd]` before prompt handling on the dedicated agent desk |
| memory distill | Transcript delta extraction exists via `adapters/codex/bin/preflight.sh distill-delta <session-id>`; opt-in proposal generation exists via `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh distill-propose <session-id> [cwd]`; automatic memory mutation remains disabled until Codex has an accepted no-tools/action contract |
| worklog state signal | Run `adapters/codex/bin/preflight.sh worklog [cwd]` to inspect configured `<agent-notes-root>` / `<worklog-board-app>` paths read-only before Codex updates notes or diagnoses board state |
| role profiles | Read `roles/README.md`, then run `adapters/codex/bin/preflight.sh role <portable-role>` to resolve Codex model/reasoning-effort settings |
| role modes | Read `roles/MODES.md`, then run `adapters/codex/bin/preflight.sh mode-info <family/mode>`; treat adapter-coupled modes as unsupported unless wrappers exist |
| hook invariants | Read `core/HOOKS.md`; run explicit preflight wrappers until Codex-native hook events exist |
| capabilities | Read `capabilities/README.md`, then run `adapters/codex/bin/preflight.sh capability-info <capability>`; do not assume Claude Skill invocation |

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

`codex_setting/` should remain minimal and explicit. It may expose `AGENTS.md`,
`README.md`, `core/`, `capabilities/`, `roles/`, `bin/`, `codex-skills`,
`codex-plugin-marketplace`, selected tools, and selected utilities, but must not expose Claude-native
`settings.json`, `commands/`, root `skills/`, or `statusline.sh` as if Codex
could consume them.

`codex_setting/tools` points at `adapters/codex/tools/`, not the entire shared
`tools/` directory. The current allowlist is:

- `memory/mem.py` (Codex-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (Codex-owned launcher for recall)

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `design-mcp` or
`web-bundle` until Codex has a documented design/tooling realization that uses
them directly.

`codex_setting/utilities` points at `adapters/codex/utilities/`, not the entire
shared `utilities/` directory. The current allowlist is:

- `agent-home.sh` (Codex-owned wrapper; no Claude runtime-home fallback)
- `artifact-root.sh`
- `agent-worklog-state.sh`
- `workflow-guard-hook.sh`
- `workflow-toggle.sh`

Do not project `dispatch-liveness.sh` until Codex has a documented transcript
liveness surface equivalent to Claude session transcript mtimes. Do not project
material/design helpers such as `extract_web_figures.py` until a Codex
capability uses them directly.

## Distillation Boundary

Claude's adapter can run a detached `claude -p` worker with tool use denied by
runtime flags. Current Codex CLI inspection shows sandbox and approval controls,
but no explicit equivalent to a no-tools worker flag. The Codex adapter therefore
separates the pipeline:

1. `distill-delta` reads Codex JSONL session logs and emits transcript delta text.
2. `distill-propose` is disabled by default. With `CODEX_DISTILL_ENABLE=1`, it
   invokes `codex exec --sandbox read-only --ask-for-approval never --ephemeral
   --ignore-rules` and writes a JSON-lines proposal.
3. The proposal is parsed by the shared `tools/memory/apply-distill-actions.py`
   applier only when `CODEX_DISTILL_APPLY=1` is explicitly set.
4. The proposal is not applied to memory automatically. A future acceptance gate
   must prove tool-free execution or provide a native no-tools flag before this
   adapter may match Claude's automatic distillation behavior.

## Worklog Boundary

Codex must treat `<agent-notes-root>` as mutable continuity state, not as harness
source. Before changing notes/routing state, run normal `write` preflight for the
target file and inspect `preflight.sh worklog` output. Codex may read/write
notes-root files only when the task is explicitly about notes, triage, feedback,
or worklog routing. It must not copy worklog-board DBs, caches, `.env*`, build
output, dispatch logs, or worktrees into this repo.
