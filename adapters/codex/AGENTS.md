# AGENTS.md — Codex Adapter Bootstrap

This is a Codex adapter router, not the portable source of truth. The semantic
hierarchy is `core/capabilities/roles -> {Claude, Codex, OpenCode}`; adapters
are siblings and none is another's reference implementation. Edit core first.

## Source Order

Codex has already loaded this file through the global instruction chain. Resolve
`<agent-home>` from `${CODEX_HOME:-$HOME/.codex}/agent-harness` (falling back to
the adapter's `agent-home.sh` resolver), and interpret every harness path below
relative to that installed root, never relative to the working repository. Do
not probe `<cwd>/core/CORE.md` or report it as a missing project file. Treat
successful root resolution as silent bootstrap bookkeeping; mention it only
when resolution fails or materially changes the task.

Read `<agent-home>/core/CORE.md` first; load the remaining documents only when
the task touches the named domain.

1. `<agent-home>/core/CORE.md`
2. `<agent-home>/core/WORKFLOW.md` for routing and tracked work
3. `<agent-home>/core/CONVENTIONS.md` for intensity, QA, roles, artifacts, and Skill rules
4. `<agent-home>/core/OPERATIONS.md` for git, worktrees, locks, and dispatch
5. `<agent-home>/core/MEMORY.md` for memory
6. `<agent-home>/capabilities/README.md`, `<agent-home>/roles/README.md`, and `<agent-home>/roles/MODES.md`

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
| lifecycle | `preflight.sh session-end`, `preflight.sh prompt-signal`, `preflight.sh turn-nudge` |
| workflow/context | `preflight.sh status`, `preflight.sh briefing`, `preflight.sh worklog` |
| memory | `preflight.sh memory`, `preflight.sh recall-gate`, `preflight.sh recall`, `preflight.sh distill-delta`, `preflight.sh distill-propose` |
| token/UI | `preflight.sh token-budget`, `preflight.sh ui-info`, `preflight.sh tui-config` |
| delegation/QA | `preflight.sh subagent-info --check`, `preflight.sh qa-policy <level> [code|research|doc|general]` |
| readiness/loops | `preflight.sh doctor [--runtime]`, `preflight.sh loop-info <oncall|note|study|drill|runtime-watch>` |
| dispatch control | `preflight.sh dispatch-wait --attempt-id <id> --max 300..600`, `preflight.sh liveness`, `preflight.sh harvest`, `preflight.sh dispatch-reconcile` |
| managed Codex | `preflight.sh managed-entry [--check] --codex-home <private-dir> --state-dir <private-dir> --workspace <dir> [--jobs <jobs.log>]` |
| install | `install-runtime-projection.sh [--install-plugin] [--skills-mode native|plugin|both]`, `check-runtime-projection.sh`, `preflight.sh runtime-projection --require-hook-trust` |

Keep Codex `/statusline` responsible for model, context, token, limit, and session footer fields. `preflight.sh status` is an on-demand harness snapshot, including git dirty/worktree/dead-branch risks. Runtime config remains user-owned; strict projection checks read authoritative App Server `hooks/list` current-hash trust and never rewrite user trust state.
The recommended footer fragment is `codex_setting/codex-config/tui-statusline.toml`; apply it only through explicit `preflight.sh tui-config`.

Registered standard+ headless owners use the checked App Server completion
supervisor: the runtime joins exact child batches and resumes the same thread once
per batch. New interactive Codex sessions opt in through
`utilities/codex-managed-entry.py`: single ingress keeps the TUI sole approval/
subscription owner and sends one bounded receipt. Parent runtime decides—Codex
gateway or Claude async-rewake/`--resume`—regardless of child. Managed completion never uses Stop continuation or a PreToolUse park; rejected steer defers once to
idle, with crash state `sent-ambiguous`. A new unmanaged interactive Codex
parent is rejected with `managed-entry-required` before registry mutation or
spawn. Finite `poll-fallback` is a low-level operator-only recovery override;
the portable owner selector and model routes cannot select it. Legacy Stop
permits exact migration harvest only.
Arbitrary detached shell output still does not auto-resume. For non-dispatch
long-running work, obey `preflight.sh
loop-info runtime-watch` and its explicit automatic-follow-up-impossible fallback
instead of ending with a detached completion promise.

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

Route by `core/WORKFLOW.md §0.2`: when a request matches one manifest
`entry-router` trigger and no exclusion, that entry is the primary route
and `direct` sets intensity, not routing. Apply §0.3 and present the
five-field card in §0.4 before material work unless scope and route are
already approved. Load full capability detail only in the acting owner or worker.

An ordinary dispatch-depth-1 owner launches through `preflight.sh dispatch-owner
--dry-run|--register|--start`, a separate low-level surface from `preflight.sh
dispatch` below: it delegates to the portable `utilities/dispatch-owner.py`
selector, which reads `profiles/dispatch-defaults.yaml` and runs the SD-22
cascade (explicit target, then hard eligibility, then configured
`depth1_owner`, then eligibility fallback) before execing only the chosen
adapter's wrapper.

Check `preflight.sh headless [--check] [--require-hook-trust] <worktree>`.
Launch registered jobs only through `preflight.sh dispatch
--dry-run|--register|--start [--require-hook-trust]` with the complete tuple in
`core/OPERATIONS.md`. Keep `capability_mode` separate from a non-owner
`worker_mode`, which must equal its portable `unit`; a dispatch-depth-1 owner is
`_kernel/owner` with no worker mode. `worker_role` and legacy `mode` are
read-only metadata, not bootstrap identity. A direct interactive launch selects
completion by the parent runtime: a live `managed-entry` Codex parent uses the
gateway and a Claude parent uses Claude resume. A new unmanaged interactive
Codex parent fails with `managed-entry-required` before registry mutation or
spawn; `dispatch-owner` also forbids completion-policy and unmanaged-poll
overrides. This parent-runtime selection does not force Stop/PreToolUse trust,
create new parent Stop state, or park the model/tool loop. Keep the parent
conversational. A human operator may use the low-level
`--allow-unmanaged-parent-poll` recovery override and then wait finitely with
`preflight.sh dispatch-wait --attempt-id <id> --max 300..600`; model routes must
not select it. Existing open or legacy attempts may use that finite recovery;
otherwise use external supervision and `preflight.sh harvest`, never an
in-model `sleep`/liveness loop.
Legacy stamped Stop state is recovery-only and permits one exact terminal
`--status all --attempt-id` harvest, never raw output or a broad selector.
Conductors use `dispatch-chain` for ordinary checked dispatch-depth-2 nodes. A sealed
2–4-way `parallel_group` uses one `dispatch-batch --parallel-group` call so all
absent first-start legs are admitted atomically and launched concurrently; do not
serialize members through separate `dispatch-chain` calls. Dispatch contract v3 atomically claims one stable
attempt row before spawn and starts no child for a duplicate claim. A standard+
Codex dispatch-depth-1 owner receives workspace-write network access for this purpose;
dispatch-depth-2 workers do not. The retired broker exposes only legacy `status`/`stop`.

`standard+` uses a dispatch-depth-1 capability owner and, when separable, dispatch-depth-2
`code-plan -> code-execute -> code-test -> code-report` stage workers.
`direct` is inline; `quick` is one registered-headless dispatch-depth-1 one-shot conductor. Dispatch depth 3 is
forbidden. Record an inline exception in plan metrics. After integration,
verification, and push, use `preflight.sh worktree-cleanup --check` before
`--apply`; SessionEnd/Stop never cleans worktrees.

For `autopilot-code`, `capability-info` and `route` print the portable pipeline contract (`code-plan>code-execute>code-test>code-report` for `standard+`).
Use native subagents only after `preflight.sh subagent-info --check`; native
subagents and registered headless workers remain distinct. A restriction on
one surface never silently extends to the other.

## Memory and Context

Memory semantics belong to the acting agent. At work intake, record `recall` or
`skip` with `preflight.sh recall-gate <cwd> ...`. For recall, use a targeted
query and retrieve full pending obligations before applying or consuming them.
Workers do not run main memory lifecycle.

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
