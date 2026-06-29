# Portable Hook Invariants

This document names the runtime-neutral invariants enforced by hook scripts.
It is not a hook registration file. Runtime adapters decide how to attach these
checks to their own event model.

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
| artifact order | `hooks/artifact-guard.sh` | `portable-check` | New tracked artifacts must be created in dependency order: spec after research/analysis, plans after spec, documents after research/analysis. | Run `hooks/artifact-guard.sh --file <path> [--session <id>]` before writes, or use an adapter wrapper. |
| git state safety | `hooks/git-state-guard.sh` | `portable-check` | Do not edit files in merge/rebase/cherry-pick/detached unsafe git states unless explicitly unlocked. | Run `hooks/git-state-guard.sh --file <path>` before file edits, or use an adapter wrapper. |
| spec read gate | `hooks/spec-skill-gate.sh`, `hooks/spec-read-marker.sh` | `portable-check` | Spec-changing capability calls in spec-backed projects require a current `prd.md` read marker. | Run `hooks/spec-read-marker.sh --file <prd.md> [--session <id>]` after actual reads, then `hooks/spec-skill-gate.sh --skill <capability> [--cwd <dir>] [--session <id>]` before spec/code capabilities. |
| memory write guard | `hooks/builtin-memory-guard.sh` | `portable-check` | Runtime-native file memory must not bypass the unified DB memory store. | Run `hooks/builtin-memory-guard.sh --file <path>` before writes, or remove the native memory feature. |
| design post-write verification | `hooks/design-postwrite.sh` | `portable-check` | Saved design HTML should get deterministic console verification. | Run `hooks/design-postwrite.sh --file <path>` after design HTML writes, or attach it to a post-write event. |
| workflow tracked signal | `utilities/workflow-guard-hook.sh` | `portable-check` | Surface tracked/untracked mode and clean stale flags. | Run `utilities/workflow-guard-hook.sh --event prompt [--cwd <dir>] [--session <id>] [--format text]` before prompt handling, and `--event start` for stale flag GC. |
| workflow mode toggle | `utilities/workflow-toggle.sh` | `portable-check` | Toggle or set the session-scoped `.untracked[.<session>]` escape-hatch flag under the artifact root. | Expose an adapter-native toggle surface; Codex uses `adapters/codex/bin/preflight.sh track [cwd] [session-id]`, Claude uses `/track`. |
| memory injection | `tools/memory/mem.py inject` | `portable-check` | Inject relevant DB memory at session start. | Run `tools/memory/mem.py inject` for text output, or `tools/memory/mem.py inject --hook` when the runtime accepts Claude-style `additionalContext`. |
| memory recall injection | `hooks/mem-recall-inject.sh` | `portable-check` | Recall signal words trigger DB recall and context injection. | Run `hooks/mem-recall-inject.sh --prompt <text> [--cwd <dir>] [--format text]` before prompt handling, or attach it to a prompt-submit event. |
| memory distillation trigger | `hooks/mem-turn-nudge.sh`, `hooks/mem-distill-dispatch.sh` | `adapter-coupled-automation` | Periodically distill session deltas into DB memory through a no-tools worker. The shared dispatcher uses `MEM_DISTILL_WORKER=<executable>` with `<mode> <model> <prompt-file>` arguments. | Provide session transcript source (`mem.py distill --source <adapter>`), detached worker invocation, and no-tools/action contract before automatic memory mutation. |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` | `portable-check` | On the dedicated agent desk, inject daily oncall report once per day. | Run `hooks/mem-briefing-inject.sh --cwd <dir> [--format text]` before prompt handling, or attach it to a prompt-submit event. |
| worklog state signal | `utilities/agent-worklog-state.sh` | `portable-check` | Surface configured `<agent-notes-root>` / `<worklog-board-app>` inventory without mutating data. | Run `utilities/agent-worklog-state.sh [cwd]` or an adapter wrapper before worklog-board or agent-notes work. |
| Herdr state integration | `hooks/herdr-agent-state.sh` | `external-integration` | Publish working/idle/blocked/release state to Herdr. | Optional external integration; not a core invariant. |

## Adapter Rule

Adapters may reuse scripts directly only when they can supply the expected input
payload and consume the expected output decision. Otherwise, the invariant must
be wrapped or reimplemented behind an adapter-native event bridge.

Current Claude Code registration lives in `adapters/claude/settings.json` and
executes concrete hook projection files under `adapters/claude/hooks/` via the
runtime projection `claude_setting/hooks`.
Codex must not consume that JSON as configuration. It can run
`adapters/codex/bin/preflight.sh write <file> [session-id]` before edits
(git state, artifact order, and native memory-file write checks),
`adapters/codex/bin/preflight.sh read <prd.md> [session-id]` after actual spec
reads, and `adapters/codex/bin/preflight.sh capability <name> [cwd] [session-id]`
before spec-changing capability work. It can also run
`adapters/codex/bin/preflight.sh mode [cwd] [session-id]` to surface tracked
or untracked workflow state as plain text. Use `adapters/codex/bin/preflight.sh
track [cwd] [session-id]` to toggle the same session-scoped workflow bypass flag
without relying on a Claude slash command. Use `adapters/codex/bin/preflight.sh
memory [cwd]` for plain-text memory injection.
Use `adapters/codex/bin/preflight.sh recall <prompt> [cwd]` to run the same
recall-signal injection logic without Claude hook JSON.
Use `adapters/codex/bin/preflight.sh briefing [cwd]` to surface the same
daily oncall briefing without Claude hook JSON.
Use `adapters/codex/bin/preflight.sh worklog [cwd]` to inspect the configured
agent-notes/worklog-board state read-only before touching that layer.
Use `adapters/codex/bin/preflight.sh design <file>` after design HTML writes
to run the same console verification without Claude hook JSON.
Use `adapters/codex/bin/preflight.sh distill-delta <session-id>` for Codex
transcript extraction. `CODEX_DISTILL_ENABLE=1 adapters/codex/bin/preflight.sh
distill-propose <session-id> [cwd]` can generate a constrained proposal, but it
must not be treated as equivalent to Claude's automatic no-tools memory worker
until the Codex adapter has an accepted no-tools/action contract.
