# Portable Hook Invariants

This document names the runtime-neutral invariants enforced by hook scripts.
It is not a hook registration file. Runtime adapters decide how to attach these
checks to their own event model.

## Verification Layers

Three distinct roles keep this contract honest. Keep the vocabulary separate —
"guard" is the enforcement mechanism, not its test.

| Layer | Role | Agent in loop? | Where |
|---|---|---|---|
| **guard** | Runtime deterministic *enforcement* — hook scripts that block, gate, or inject at the event boundary. | No | The Invariant Catalog below (`hooks/*-guard.sh`, `utilities/*-hook.sh`, adapter hook bridges). |
| **conformance** | Deterministic *verification* that guards, hook bridges, and adapters honor this contract — exact assertions, no model. Covers the `test` status class plus cross-adapter parity. | No | `hooks/portable-guards.test.sh`, `tools/check-adaptation-boundary.sh` (+ per-adapter mirrors). |
| **drill** | Behavioral *regression* — whether the agent follows the rules on a live scenario (golden set). Covers only what cannot be made deterministic. | Yes | `loops/drill/`. |

Design bias (deterministic-first, §0.5): push a check *down* this table when you
can — out of **drill** (agent behavior) into **guard** + **conformance**
(mechanism + deterministic test). Reserve drill for residue that genuinely needs
an agent in the loop. A hook's output shape is deterministic, so it belongs in
conformance, never drill.

The drill **runner** also invokes the conformance layer directly, as a separate
deterministic pre-stage — not a drill case, no agent in loop — before it runs
any behavioral case. This keeps conformance firing from depending solely on the
preflight doctor path, without blurring the conformance/drill distinction above.

## Status Classes

| Status | Meaning |
|---|---|
| `portable-check` | Core decision logic is runtime-neutral and has a CLI entry point. It may also accept Claude hook JSON for compatibility. |
| `adapter-payload-wrapper` | Primarily translates a runtime event payload into a portable decision. Needs adapter-specific wrapper for non-Claude runtimes. |
| `adapter-coupled-automation` | Depends on a concrete runtime session lifecycle, status UI, MCP, or headless worker process. Other runtimes must implement their own equivalent or mark unsupported. |
| `external-integration` | Owned by an external integration and not part of the portable contract. |
| `test` | Local regression test for a hook implementation. |

## Invariant Catalog

| Invariant | Current script | Status | Portable meaning | Non-Claude adapter requirement |
|---|---|---|---|---|
| artifact order | `hooks/artifact-guard.sh` | `portable-check` | Writes fail closed outside the canonical artifact root (linked worktrees may not write their local `.agent_reports`/`.claude_reports` snapshot), and a route-backed write under `spec/` requires the active route to have declared `spec_touch` with a `spec/` write scope. The broader creation-order convention (spec after research/analysis, plans after spec, documents after research/analysis) is routing convention, not a mechanical block. | Run `hooks/artifact-guard.sh --file <path> [--session <id>]` before writes, or use an adapter wrapper. |
| git state safety | `hooks/git-state-guard.sh` | `portable-check` | Do not edit files in merge/rebase/cherry-pick/detached unsafe git states unless explicitly unlocked. | Run `hooks/git-state-guard.sh --file <path>` before file edits, or use an adapter wrapper. |
| worktree path isolation | `hooks/worktree-path-guard.sh` | `portable-check` | Main-task worktrees must be sibling directories `<repo>-wt/<slug>` (OPERATIONS §5.10 ②), never inside the repo. Deny the runtime-native worktree tool whose default lands in-repo, and deny a `git worktree add` whose target path is outside `<repo>-wt/`; fail open outside a git repo, on non-add worktree subcommands, and under `WORKTREE_GUARD_BYPASS=1`. | Run `hooks/worktree-path-guard.sh --tool <EnterWorktree\|Bash> [--command <cmd>] [--cwd <dir>] [--session <id>]` before worktree creation. Only the `git worktree add` path check is portable; the built-in-worktree-tool deny is Claude-native — a runtime without an EnterWorktree-style tool (Codex, OpenCode) has no such surface to deny and must not claim it (disclose in ADAPTATION_INVENTORY, no overclaim). |
| spec read gate | `hooks/spec-skill-gate.sh`, `hooks/spec-read-marker.sh` | `portable-check` | Spec-changing capability calls in spec-backed projects require a current same-session read marker for at least one governing spec candidate — the root `spec/prd.md` or a one-level `spec/<slug>/prd.md` sub-spec (`_internal` snapshots excluded). Freshness is per candidate: the marker's recorded mtime must be at least that candidate's current mtime. | Run `hooks/spec-read-marker.sh --file <prd.md> [--session <id>]` after actual reads, then `hooks/spec-skill-gate.sh --skill <capability> [--cwd <dir>] [--session <id>]` before spec/code capabilities. |
| core first gate | `hooks/core-first-guard.sh`, `hooks/core-read-marker.sh` | `portable-check` | Adapter edits require a current-session `core/*.md` read marker so adapter changes are derived from the model-neutral contract. | Run `hooks/core-read-marker.sh --file <core-doc> [--session <id>]` after actual core reads, then `hooks/core-first-guard.sh --file <adapter-target> [--session <id>]` before adapter writes. |
| memory write guard | `hooks/builtin-memory-guard.sh` | `portable-check` | Runtime-native file memory must not bypass the unified DB memory store. | Run `hooks/builtin-memory-guard.sh --file <path>` before writes, or remove the native memory feature. |
| design post-write verification | `hooks/design-postwrite.sh` | `portable-check` | Saved design HTML should get deterministic console verification. | Run `hooks/design-postwrite.sh --file <path>` after design HTML writes, or attach it to a post-write event. |
| spec sync nudge | `hooks/spec-sync-nudge.sh` | `portable-check` | In a spec-backed project, a source edit that removes a value/identifier still described in `spec/*.md` should surface those spec lines so the corresponding spec text is synced as part of the change. Read-only: emits context only, never blocks. | Run `hooks/spec-sync-nudge.sh --file <path> [--old <s>] [--new <s>] [--cwd <dir>] [--format text]` after edits, or attach it to a post-write event that supplies the edited path and old/new strings. |
| memory injection | `tools/memory/mem.py inject` | `portable-check` | Inject relevant DB memory at session start. | Run `tools/memory/mem.py inject` for text output, or `tools/memory/mem.py inject --hook` when the runtime accepts Claude-style `additionalContext`; adapters may keep automatic session-start injection opt-in when the runtime can fire start events on resume or compact. |
| agent-initiated memory retrieval | `tools/memory/recall.sh`, `tools/memory/mem.py recall` | `portable-check` | The acting agent decides when prior context is relevant, then invokes scoped retrieval. Ranking and limits organize results after that decision; prompt-submit hooks do not classify every prompt or inject threshold-qualified hits. | Expose an explicit adapter-native helper. Keep retrieval project-scoped by default and widen scope only when the agent chooses to do so. |
| retired automatic recall shim | `hooks/mem-recall-inject.sh` | `portable-check` | Compatibility no-op for stale installed projections. It drains an old prompt payload, emits no context, and exits successfully. | Do not register it in current prompt hooks; expose the explicit retrieval helper above. |
| memory distillation trigger | `hooks/mem-turn-nudge.sh`, `hooks/mem-distill-dispatch.sh` | `adapter-coupled-automation` | On an interactive main session only, periodically distill session deltas into DB memory through a no-tools worker. `AGENT_SESSION_ROLE=worker` and adapter compatibility markers make both hooks silent no-ops before counters, locks, or model calls. The shared dispatcher uses `MEM_DISTILL_WORKER=<executable>` with `<mode> <model> <prompt-file>` arguments. | Provide session transcript source (`mem.py distill --source <adapter>`), detached worker invocation, no-tools/action contract, and the same main/worker gate before automatic memory mutation. Deterministic safety hooks remain active in workers. |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` | `portable-check` | On the dedicated agent desk, inject daily oncall report once per day. | Run `hooks/mem-briefing-inject.sh --cwd <dir> [--format text]` before prompt handling, or attach it to a prompt-submit event. |
| worklog state signal | `utilities/agent-worklog-state.sh` | `portable-check` | Surface configured `<agent-notes-root>` / `<worklog-board-app>` inventory without mutating data. | Run `utilities/agent-worklog-state.sh [cwd]` or an adapter wrapper before worklog-board or agent-notes work. |
| runtime hook output protocol | adapter hook bridges | `adapter-payload-wrapper` | Hook stdout must match the owning runtime's hook protocol exactly. Context-injection hooks emit the runtime's structured context object; side-effect-only lifecycle hooks keep stdout empty unless that runtime explicitly accepts a structured success object. Portable helper text is never forwarded as raw hook stdout. | Each adapter must document its hook output contract, test the exact stdout shape for every native hook bridge, and route diagnostic/helper text to logs or stderr only when the runtime accepts it. |
| Herdr state integration | `hooks/herdr-agent-state.sh` | `external-integration` | Publish working/idle/blocked/release state to Herdr. | Optional external integration; not a core invariant. |
| stage-dispatch reminder | `hooks/stage-dispatch-reminder.sh` | `portable-check` | SD-11: when a dispatch-depth-1 conductor at standard+ intensity is about to invoke a `code-{plan,execute,test,report}` sub-skill **in-session** (env `CLAUDE_CODE_CHILD_SESSION=1`, `AGENT_DISPATCH_DEPTH=1`, `AGENT_DISPATCH_INTENSITY∈{standard,strong,thorough,adversarial}`), surface a reminder to dispatch the stage as a dispatch-depth-2 headless session instead. **Soft / non-deny** (fail-open): emits `additionalContext` only, never blocks — the hook cannot tell a legitimate headless-unavailable fallback from a mistake (§8.5.2). Recursion guard: no-op under `MEM_DISTILL=1`. | Run `hooks/stage-dispatch-reminder.sh --skill <name> [--depth <n>] [--intensity <i>]` before a Skill call, or attach it to a pre-tool Skill event. |
| conductor Stop gate | `hooks/conductor-stop-gate.sh` | `portable-check` (**UNREGISTERED — conditional**) | SD-14b: block a dispatch-depth-1 conductor's turn-end while it still has open dispatch-depth-2 stage children (`parent=<self-slug>` open rows in jobs.log). ALIVE children → block ("poll with dispatch-wait and harvest"); SUSPECT/DEAD → block with a **diagnose** action (not "keep waiting"). Loop guard: no-op when `stop_hook_active`. **Held / not registered**: `claude -p` does not fire `Stop` and (CC #38651) a registered Stop hook empties the `-p` result output, which would break harvesting — so this is kept on disk (logic+CLI) but absent from `settings.json`. SD-14 ships via the wrapper depth_note one-shot clause + `utilities/dispatch-wait.sh`. | Register only on a runtime whose headless mode fires `Stop` without corrupting result output; run `hooks/conductor-stop-gate.sh --self-slug <slug> [--jobs <path>] [--stop-active true\|false]` as a Stop event. |

## Adapter Rule

Adapters may reuse scripts directly only when they can supply the expected input
payload and consume the expected output decision. Otherwise, the invariant must
be wrapped or reimplemented behind an adapter-native event bridge.

Adapter hook bridges own the final runtime output protocol. A portable helper can
print human-readable status for explicit CLI use, but a native runtime hook must
not forward that text unless the runtime accepts it for that hook event. For
example, a context hook may emit `hookSpecificOutput.additionalContext` when the
runtime supports it, while a lifecycle side-effect hook such as a session-end
sync may need to perform the mutation with empty stdout or a minimal structured
success object so the runtime does not attempt to parse helper text as hook
JSON.

Current Claude Code registration lives in `adapters/claude/settings.json` and
executes concrete hook projection files under `adapters/claude/hooks/` via the
runtime projection `claude_setting/hooks`.
Codex must not consume that JSON as configuration. It can run
`adapters/codex/bin/preflight.sh write <file> [session-id]` before edits
(git state, artifact order, core-first adapter edit gate, and native memory-file write checks),
`adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual spec
reads, and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`
before spec-changing capability work. It can also run
`adapters/codex/bin/preflight.sh prompt-signal [cwd] [session-id]` to carry the
fuller routing contract as a worker-startup/manual subcommand, not a per-turn
injection. Use `adapters/codex/bin/preflight.sh
memory [cwd]` for plain-text memory injection; Codex automatic SessionStart
context is opt-in via `CODEX_SESSION_MEMORY_INJECT=1`.
Use `adapters/codex/bin/preflight.sh recall <query> [cwd]` when the agent
chooses to retrieve memory explicitly; it is not a prompt-hook classifier.
Use `adapters/codex/bin/preflight.sh briefing [cwd]` to surface the same
daily oncall briefing without Claude hook JSON.
Use `adapters/codex/bin/preflight.sh worklog [cwd]` to inspect the configured
agent-notes/worklog-board state read-only before touching that layer.
Use `adapters/codex/bin/preflight.sh design <file>` after design HTML writes
to run the same console verification without Claude hook JSON.
Use `adapters/codex/bin/preflight.sh distill-delta <session-id>` for Codex
transcript extraction. `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh
distill-propose <session-id> [cwd]` can generate a constrained proposal, but it
is a manual preview surface and does not auto-apply unless the apply and
contract-accepted env gates are explicit. Codex adapter-owned `session-end` and
`turn-nudge` paths are the verified automatic realization: after the documented
read-only `codex exec` tool-free proof, they default to automatic apply and opt
out with `CODEX_DISTILL_ENABLE=0`. They run only for an interactive main;
dispatch/title/distill/loop workers make both paths silent no-ops under D-42.
Use `adapters/opencode/bin/preflight.sh distill-delta <session-id>` for
OpenCode transcript extraction through `opencode export`. OpenCode's no-tools
worker contract is verified (`opencode run --pure --agent <distiller>` with all
tools disabled), so `distill-propose` runs the worker and the plugin
`event`/`session.idle` trigger auto-distills via `preflight.sh session-end`
(debounced, enabled by default for main sessions; opt out
`OPENCODE_DISTILL_ENABLE=0`). Worker sessions keep plugin write/read guards and
liveness heartbeats but skip automatic memory context and session-idle distill.
