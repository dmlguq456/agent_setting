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
| Custom agents | `adapters/codex/agents/<role>.toml` generated from `roles/README.md` | `codex_setting/codex-agents` |
| Plugin marketplace | `adapters/codex/.agents/plugins/marketplace.json` plus `adapters/codex/plugins/agent-harness-codex` | `codex_setting/codex-plugin-marketplace` |
| Hook bridge | `adapters/codex/hooks/hooks.json`, `adapters/codex/hooks/pretooluse-write-guard.py`, `adapters/codex/hooks/posttooluse-design-check.py` | `codex_setting/codex-hooks` |
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
guidance for them, but must run the adapter visual harness before claiming full
support. `capability-info` reports `status=tool-contract` for those entries.

`roles/modes/material/browser-fetch.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh browser-fetch --check <url>` verifies rendered
browser access through `adapters/codex/tools/material/` and reports exit 69
when the local Playwright browser stack is unavailable.

`roles/modes/material/data-script.md` is the first material mode with a
Codex-owned executable tool-contract surface:
`adapters/codex/bin/preflight.sh data-script --check <script.py>` verifies
generated Python analysis scripts through `adapters/codex/tools/material/`.

`roles/modes/material/figure-gen.md` has a Codex-owned executable tool-contract
surface:
`adapters/codex/bin/preflight.sh figure-gen --check <script.py>` verifies
generated matplotlib/seaborn figure scripts through
`adapters/codex/tools/material/`.

`roles/modes/material/pdf-extract.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh pdf-extract --check <file.pdf>` verifies
local PDF text extraction through `adapters/codex/tools/material/` and reports
exit 69 when the local extractor is unavailable.

`roles/modes/material/web-image-search.md` has a Codex-owned executable
tool-contract surface:
`adapters/codex/bin/preflight.sh web-image-search --check <query>` verifies a
configured image-search provider command through `adapters/codex/tools/material/`
and reports exit 69 when no provider is configured.

`roles/modes/qa/security-review.md` is portable read-only mode guidance for
Codex. It is consumed with Codex file and git diff tools and does not project
or invoke Claude's `/security-review` slash command.

`roles/modes/qa/test.md` has a Codex-owned executable tool-contract surface:
`adapters/codex/bin/preflight.sh verification-runner --check -- <command>`
checks explicit verification commands and the same wrapper can execute them
with a bounded timeout.

The boundary guard checks that generated Codex skills and the generated Codex
plugin remain in sync, and that neither surface is built from Claude Skill
files.

## Native Custom Agent Surface

Codex supports custom subagents through TOML files under `$CODEX_HOME/agents/`
or project `.codex/agents/`. This adapter materializes those role profiles as
`adapters/codex/agents/<role>.toml`, generated from `roles/README.md` by
`adapters/codex/bin/sync-native-agents.py` and projected as
`codex_setting/codex-agents`.

Each file defines Codex's required custom agent fields (`name`, `description`,
and `developer_instructions`) while leaving concrete model and reasoning
choices to `adapters/codex/bin/preflight.sh role <portable-role>` and the
runtime's parent session/config inheritance. Do not project Claude Agent files
or OpenCode Agent files into Codex.

Validation is currently structural plus install-path validation. The boundary
guard verifies generated TOML fields, portable role references, role-map
resolution, and absence of non-Codex adapter paths. Codex CLI 0.142.x exposes
`codex debug prompt-input` for bootstrap/Skill/plugin discovery, but it does
not expose a `codex debug agent` listing surface; add runtime discovery coverage
when Codex exposes one.

## Native Hook Surface

Codex supports lifecycle hooks through `hooks.json` and inline config. This
adapter materializes a Codex-native hook projection under `adapters/codex/hooks/`.
The `SessionStart` bridge calls `adapters/codex/bin/preflight.sh start` and
`memory` for stale workflow cleanup and memory context. The `UserPromptSubmit`
bridge calls `mode`, `recall`, and `briefing` for prompt-time workflow and memory
signals. The write bridge registers `PreToolUse` for write/edit/patch tools and
calls `adapters/codex/bin/preflight.sh write <file> <session-id>`, which runs
the portable artifact-order, git-state, and memory-write guards. The design
bridge registers `PostToolUse` for the same write/edit/patch surface and calls
`adapters/codex/bin/preflight.sh design <file>` for saved design HTML files.

Do not project Claude `hooks/` or `settings.json` into Codex. Use
`codex_setting/codex-hooks` as the install source, and keep explicit
`preflight.sh` calls as fallback where Codex hooks are disabled or untrusted.
The lifecycle hooks are informational/context bridges and do not replace
deterministic write guards. The design hook is a console-check alert path, not a
full render/screenshot visual harness.

Codex CLI 0.142.x exposes `codex debug prompt-input`, but not a hook listing or
hook firing debug surface. Current tests validate `hooks.json` structure and
execute the concrete bridge scripts with synthetic Codex hook payloads; add a
runtime hook discovery test when Codex exposes a hook debug surface.

## Explicit Non-Support

Codex must not consume these Claude-native files as native configuration:

| Claude-native surface | Codex status |
|---|---|
| `adapters/claude/settings.json` | Not consumable; Codex needs wrapper/preflight equivalents |
| `adapters/claude/commands/` | Not consumable; command-like harness entries use Codex-native Skills and the installable `agent-harness-codex` plugin |
| `skills/*/SKILL.md` | Compatibility reference only; Codex should start from `capabilities/README.md` |
| `adapters/claude/statusline.sh` | Not consumable; input schema is Claude statusline JSON |
| `adapters/claude/track-toggle.sh` | Do not consume; portable semantics live in `utilities/workflow-toggle.sh`, and Codex exposes them through `preflight.sh track` |
| `adapters/claude/CLAUDE.md` | Reference only; not bootstrap |
| `adapters/claude/agents/*.md` | Reference only; Codex custom agents are generated from `roles/README.md` |
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
| role modes | Read `roles/MODES.md`, then run `adapters/codex/bin/preflight.sh mode-info <family/mode>`; treat adapter-coupled modes as unsupported unless wrappers exist, obey `fallback=reference-only`, and satisfy any named `tool_contract` / `tool_contract_check` before claiming tool-contract modes |
| hook invariants | `adapters/codex/hooks/pretooluse-write-guard.py` realizes write guards through Codex `PreToolUse`; `posttooluse-design-check.py` realizes design HTML console checks through `PostToolUse`; run explicit preflight wrappers for events not yet covered by native hooks |
| capabilities | Read `capabilities/README.md`, then run `adapters/codex/bin/preflight.sh capability-info <capability>`; do not assume Claude Skill invocation |

## Model Mapping

Codex exposes concrete choices through environment or config and resolves them
with `adapters/codex/bin/preflight.sh role <portable-role>`:

```text
AGENT_MODEL_FAST
AGENT_MODEL_DEEP
AGENT_MODEL_EXTERNAL
AGENT_MODEL_ORCHESTRATOR
AGENT_REASONING_FAST
AGENT_REASONING_DEEP
AGENT_REASONING_EXTERNAL
AGENT_REASONING_ORCHESTRATOR
AGENT_EXTERNAL_CMD
```

When no concrete model is configured, the adapter reports `codex-default` and
`runtime-default`. `external adversary` remains unavailable unless
`AGENT_MODEL_EXTERNAL` or `AGENT_EXTERNAL_CMD` is configured.

## Current Projection Boundary

`codex_setting/` should remain minimal and explicit. It may expose `AGENTS.md`,
`README.md`, `core/`, `capabilities/`, `roles/`, `bin/`, `codex-skills`,
`codex-agents`, `codex-plugin-marketplace`, `codex-hooks`, selected tools, and selected utilities, but must not expose Claude-native
`settings.json`, `commands/`, root `skills/`, `hooks/`, or `statusline.sh` as if Codex
could consume them.

`codex_setting/tools` points at `adapters/codex/tools/`, not the entire shared
`tools/` directory. The current allowlist is:

- `memory/mem.py` (Codex-owned launcher for the shared memory CLI)
- `memory/apply-distill-actions.py`
- `memory/recall.sh` (Codex-owned launcher for recall)
- `material/browser-fetch.sh` (Codex-owned launcher for rendered web page extraction)
- `material/data-script.sh` (Codex-owned launcher for Python data-analysis scripts)
- `material/figure-gen.sh` (Codex-owned launcher for generated matplotlib figure scripts)
- `material/pdf-extract.sh` (Codex-owned launcher for local PDF text extraction)
- `material/web-image-search.sh` (Codex-owned launcher for configured image search providers)
- `qa/verification-runner.sh` (Codex-owned launcher for explicit verification commands)
- `design/visual-harness.sh` (Codex-owned launcher for render/screenshot/console checks)

Do not project `build-manifest.py`: it is a harness development tool that reads
Claude adapter skills, agents, and settings. Do not project `web-bundle` until
Codex has a documented design/tooling realization that uses it directly. The
shared `design-mcp` package is not projected wholesale; Codex exposes only the
adapter-owned visual harness launcher.

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
   applier only when both `CODEX_DISTILL_APPLY=1` and
   `CODEX_DISTILL_CONTRACT_ACCEPTED=1` are explicitly set.
4. The proposal is not applied to memory automatically. The acceptance gate
   must prove tool-free execution or provide a native no-tools flag before this
   adapter may match Claude's automatic distillation behavior.

## Worklog Boundary

Codex must treat `<agent-notes-root>` as mutable continuity state, not as harness
source. Before changing notes/routing state, run normal `write` preflight for the
target file and inspect `preflight.sh worklog` output. Codex may read/write
notes-root files only when the task is explicitly about notes, triage, feedback,
or worklog routing. It must not copy worklog-board DBs, caches, `.env*`, build
output, dispatch logs, or worktrees into this repo.
