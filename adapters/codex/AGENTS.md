# AGENTS.md — Codex Adapter Bootstrap

This is a Codex adapter router, not the portable source of truth. The semantic
hierarchy is `core/capabilities/roles -> {Claude, Codex, OpenCode}`; adapters
are siblings and none is another's reference implementation. Edit core first.

## Source Order

Read `core/CORE.md` first; load the remaining documents only when the task
touches the named domain.

1. `core/CORE.md`
2. `core/WORKFLOW.md` for routing and tracked work
3. `core/CONVENTIONS.md` for intensity, QA, roles, artifacts, and Skill rules
4. `core/OPERATIONS.md` for git, worktrees, locks, and dispatch
5. `core/MEMORY.md` for memory
6. `capabilities/README.md`, `roles/README.md`, and `roles/MODES.md`

For runtime-surface or parity changes, verify current official Codex/Claude
documentation, then inspect the local realization. Separate runtime support,
local projection, and parity gaps; plan a checked fallback.

## Runtime Mapping

- `AGENT_HOME` is the installed harness root. Resolve artifacts through `utilities/artifact-root.sh`; linked worktrees write the primary checkout's `.agent_reports/`.
- Portable model roles remain vendor-neutral. Resolve them with `preflight.sh role <portable-role|role-profile|pipeline-stage>`.
- Capabilities come from `capabilities/`; Codex-native generated Skills/plugin, agents, and modes live under `adapters/codex/`. Expose them through `codex_setting/codex-plugin-marketplace`, `codex_setting/codex-agents`, and `codex_setting/codex-modes`.
- Hooks are Codex bridges under `codex_setting/codex-hooks`; never project Claude settings, commands, hooks, or allowedTools.
- Before using a capability or mode, run `adapters/codex/bin/preflight.sh capability-info <capability>` or `preflight.sh mode-info <family/mode>` and obey named `tool_contract`, `tool_contract_check`, `runtime_surface`, and `fallback`.
- Before edits run `preflight.sh write <file> [session-id]`. Read the governing core file first for `adapters/**`; mark actual core/spec reads with `preflight.sh read <file> [session-id]`. Run `preflight.sh capability <name> [cwd] [session-id]` for spec changes.
- Shell/Bash/`functions.exec_command` reads and writes have targeted hook coverage; use explicit read/write/design preflight for ambiguous guarded I/O.

Detailed lifecycle and edge-case contracts live in `adapters/codex/README.md`
and `ADAPTATION.md`; command output is authoritative for current support.

## Command Surface

| Need | Command |
|---|---|
| lifecycle | `preflight.sh start`, `preflight.sh session-end`, `preflight.sh mode`, `preflight.sh prompt-signal`, `preflight.sh turn-nudge` |
| workflow/context | `preflight.sh status`, `preflight.sh track`, `preflight.sh briefing`, `preflight.sh worklog` |
| memory | `preflight.sh memory`, `preflight.sh recall`, `preflight.sh distill-delta`, `preflight.sh distill-propose` |
| token/UI | `preflight.sh token-budget`, `preflight.sh ui-info`, `preflight.sh tui-config` |
| delegation/QA | `preflight.sh subagent-info --check`, `preflight.sh qa-policy <level> [code|research|doc|general]` |
| readiness/loops | `preflight.sh doctor [--runtime]`, `preflight.sh loop-info <oncall|note|study|drill|runtime-watch>` |
| install | `install-runtime-projection.sh [--install-plugin] [--skills-mode native|plugin|both]`, `check-runtime-projection.sh`, `preflight.sh runtime-projection --require-hook-trust` |

Keep Codex `/statusline` responsible for model, context, token, limit, and session footer fields. `preflight.sh status` is an on-demand harness snapshot, including git dirty/worktree/dead-branch risks. Runtime config remains user-owned; `session_end=stop-alias` is only a projection-check status.
The recommended footer fragment is `codex_setting/codex-config/tui-statusline.toml`; apply it only through explicit `preflight.sh tui-config`.

Long-running completion delivery is governed by `preflight.sh loop-info
runtime-watch`; background shell output alone does not resume a completed Codex
turn. Obey its native scheduled follow-up, current-turn wait/poll, or explicit
automatic-follow-up-impossible fallback instead of ending with a detached
completion promise.

## Tool Contracts

Before claiming support, run the relevant check:

- `preflight.sh visual-harness <file.html>`
- `preflight.sh browser-fetch --check <url>`
- `preflight.sh data-script --check <script.py>`
- `preflight.sh figure-gen --check <script.py>`
- `figure-gen --verify-report <manifest.json> <report.md>`
- `preflight.sh pdf-extract --check <file.pdf>`
- `preflight.sh web-image-search --check <query>`
- `preflight.sh verification-runner --timeout <seconds> -- <command>`
- `preflight.sh claim-verify --check <claim>`
- `preflight.sh permissions` and `preflight.sh mcp [--check]`

Exit 69 means the local tool contract is unavailable; use the reported fallback
or mark the adapter row unverified/unsupported. Never borrow a Claude-native
tool to claim Codex parity.

## Dispatch

Select the primary capability semantically per `core/WORKFLOW.md §0.2` and use
its §0.3 pre-execution gate when applicable.

Check `preflight.sh headless [--check] [--require-hook-trust] <worktree>`.
Launch only registered jobs through
`preflight.sh dispatch --dry-run|--register|--start [--require-hook-trust]`
with explicit worktree, slug, capability, mode, QA, intensity, depth, parent,
worker role, owner, and model choice/inheritance. Monitor with
`preflight.sh liveness [jobs.log]`; harvest with `preflight.sh harvest`.
Before a standard+ conductor starts, depth 0 prepares the shared non-model
broker through `preflight.sh broker ensure --jobs <canonical-jobs>`; the wrapper
does this idempotently on `--start`. Conductors use `dispatch-chain`, which sends
all same/cross-harness depth-2 targets through that broker rather than recursively
starting adapter CLIs.

`standard+` uses a depth-1 capability owner and, when separable, depth-2
`code-plan -> code-execute -> code-test -> code-report` stage workers.
`direct` is inline; `quick` is one depth-1 one-shot worker. Depth 3 is
forbidden. Record an inline exception in plan metrics. After integration,
verification, and push, use `preflight.sh worktree-cleanup --check` before
`--apply`; SessionEnd/Stop never cleans worktrees.

For `autopilot-code`, `capability-info` and `route` print the portable pipeline contract (`code-plan>code-execute>code-test>code-report` for `standard+`).
Use native subagents only after `preflight.sh subagent-info --check`; native
subagents and registered headless workers remain distinct. A restriction on
one surface never silently extends to the other.

## Memory and Context

Memory semantics belong to the acting agent. Use a targeted `preflight.sh recall
"<query>" [cwd]`; retrieve a full pending obligation before applying and
consuming it. Workers do not run main memory lifecycle.

`preflight.sh token-budget` exposes exact-session telemetry. The normal, unknown, repeated-band, and validated-native states inject zero bytes; a verified
tight/critical transition may emit one directive of at most 240 UTF-8 bytes.
Pressure changes optional response prose only—never intensity, dispatch/depth,
model role, required input, tools/tests, safety, validation, or guards.
`token-budget-experiment.py` is production-disabled; static bytes and counters
are not token, billing, savings, cost, or ROI estimates. Native budget config is
read-only unless the user explicitly opts into a separately validated feature.

Do not run drill automatically. Do not edit runtime-owned credentials, sessions,
logs, caches, databases, or `$CODEX_HOME/config.toml`.

## Response Policy

Portable behavior contract = `roles/response-policy.md`.

- **Audience-language first** — user artifacts default to the user's current communication language unless a stronger audience/repository contract applies.
- Keep responses concise, match promises with same-turn action, verify before asserting, and follow current conventions.
- Ask only for genuinely non-obvious or destructive choices. Continue reversible in-flow work and its implied validation, records, commit, and push.

## Compatibility Boundary

Claude/OpenCode files are sibling references, not Codex bootstrap input. Portable
meaning comes from `core/`, `capabilities/`, and `roles/`; map it to Codex
tools, approval, sandbox, lifecycle, and discovery.
