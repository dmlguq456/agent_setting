# Portable Hook Invariants

This document names the runtime-neutral invariants enforced by hook scripts.
It is not a hook registration file. Runtime adapters decide how to attach these
checks to their own event model.

## Status Classes

| Status | Meaning |
|---|---|
| `portable-check` | Core decision logic is runtime-neutral, but the current script may still parse Claude hook JSON. |
| `adapter-payload-wrapper` | Primarily translates a runtime event payload into a portable decision. Needs adapter-specific wrapper for non-Claude runtimes. |
| `adapter-coupled-automation` | Depends on Claude session lifecycle, status, MCP, or headless `claude -p`. Other runtimes must implement their own equivalent or mark unsupported. |
| `external-integration` | Owned by an external integration and not part of the portable contract. |
| `test` | Local regression test for a hook implementation. |

## Invariant Catalog

| Invariant | Current script | Status | Portable meaning | Non-Claude adapter requirement |
|---|---|---|---|---|
| artifact order | `hooks/artifact-guard.sh` | `adapter-payload-wrapper` | New tracked artifacts must be created in dependency order: spec after research/analysis, plans after spec, documents after research/analysis. | Provide file path and session id to the check before writes, or run an equivalent pre-write wrapper. |
| git state safety | `hooks/git-state-guard.sh` | `adapter-payload-wrapper` | Do not edit files in merge/rebase/cherry-pick/detached unsafe git states unless explicitly unlocked. | Run before file edits with target path. |
| spec read gate | `hooks/spec-skill-gate.sh`, `hooks/spec-read-marker.sh` | `adapter-payload-wrapper` | Spec-changing capability calls in spec-backed projects require a current `prd.md` read marker. | Record actual reads and check markers before spec/code capabilities. |
| memory write guard | `hooks/builtin-memory-guard.sh` | `adapter-payload-wrapper` | Runtime-native file memory must not bypass the unified DB memory store. | Block writes to runtime memory-file paths or remove the native memory feature. |
| design post-write verification | `hooks/design-postwrite.sh` | `adapter-coupled-automation` | Saved design HTML should get deterministic console verification. | Provide an equivalent browser/console checker or report unsupported. |
| workflow tracked signal | `utilities/workflow-guard-hook.sh` | `adapter-payload-wrapper` | Surface tracked/untracked mode and clean stale flags. | Attach to session/prompt start or expose an explicit wrapper reminder. |
| memory injection | `tools/memory/mem.py inject --hook` | `adapter-payload-wrapper` | Inject relevant DB memory at session start. | Map the injection output to the runtime's context mechanism. |
| memory recall injection | `hooks/mem-recall-inject.sh` | `adapter-coupled-automation` | Recall signal words trigger DB recall and context injection. | Provide prompt-submit event payload and context injection support. |
| memory distillation trigger | `hooks/mem-turn-nudge.sh`, `hooks/mem-distill-dispatch.sh` | `adapter-coupled-automation` | Periodically distill session deltas into DB memory through a no-tools worker. | Provide session transcript source, detached worker invocation, and no-tools/action contract. |
| oncall briefing injection | `hooks/mem-briefing-inject.sh` | `adapter-coupled-automation` | On the dedicated agent desk, inject daily oncall report once per day. | Provide cwd/session prompt event and context injection, or mark unsupported. |
| Herdr state integration | `hooks/herdr-agent-state.sh` | `external-integration` | Publish working/idle/blocked/release state to Herdr. | Optional external integration; not a core invariant. |

## Adapter Rule

Adapters may reuse scripts directly only when they can supply the expected input
payload and consume the expected output decision. Otherwise, the invariant must
be wrapped or reimplemented behind an adapter-native event bridge.

Current Claude Code registration lives in `adapters/claude/settings.json`.
Codex must not consume that JSON as configuration; it should run explicit
preflight wrappers for `artifact order`, `git state safety`, and `spec read gate`
until a native hook/event bridge exists.
