# CLAUDE.md — Claude Adapter Bootstrap

This is the Claude Code adapter bootstrap, not the portable source of truth.
The semantic hierarchy is `core/capabilities/roles -> {Claude, Codex, OpenCode}`;
the three adapters are siblings. Edit portable sources first.

## Source Order

Read `core/CORE.md` first; load the remaining documents only when the task
touches the named domain.

1. `core/CORE.md`
2. `core/WORKFLOW.md` for routing and tracked work
3. `core/CONVENTIONS.md` for intensity, QA, roles, artifacts, and Skill rules
4. `core/OPERATIONS.md` for git, worktrees, locks, and dispatch
5. `core/MEMORY.md` for memory
6. `capabilities/README.md`, `roles/README.md`, and `roles/MODES.md` for task behavior

## Runtime Router

- Treat `AGENT_HOME` as the installed harness root.
- Resolve the canonical artifact root with `utilities/artifact-root.sh`; linked worktrees write the primary checkout's `.agent_reports/`, and legacy `.claude_reports/` is only a fallback.
- Use portable model roles, never vendor model names, in shared artifacts.
- Claude-native Skills, Agents, modes, hooks, commands, and settings live under `adapters/claude/`; `skills/` is a compatibility mirror.
- Before adapter edits, read the governing core contract and run the applicable write guard. Before spec changes, read the current PRD and use the spec capability gate.
- Run deterministic guards directly when hook execution is unavailable or untrusted.
- Task-specific detail is progressively disclosed through the selected Skill and adapter README/ADAPTATION docs; do not preload unrelated procedures.

## Routing and Execution

Select the primary capability semantically per `core/WORKFLOW.md §0.2` (WORKFLOW §0.2) and answer the pre-execution gate in §0.3 when applicable. Read-only orientation and targeted memory recall do not themselves invoke a capability. For spec-backed work, satisfy the spec-read gate before mutation.

`autopilot-code` follows the portable intensity graph:

- `direct`: inline, no durable plan.
- `quick`: one depth-1 one-shot worker with micro-plan, plan-check-lite, focused verification, and concise report.
- `standard+`: `code-plan -> code-execute -> code-test -> code-report`, optional `code-refine`, file-only handoff, and the dispatch/fallback rules in `core/OPERATIONS.md §5.10`.

Before compiling a standard+ route, depth 0 runs
`python3 "$AGENT_HOME/utilities/dispatch-broker.py" ensure --jobs "${AGENT_DISPATCH_JOBS:-$AGENT_HOME/.dispatch/jobs.log}"`
and binds the reported broker root/instance to the conductor. The dispatch
wrapper repeats this idempotently before start. Every same/cross-harness
depth-2 headless target then uses `stage-dispatch-fallback.py`; Claude native
subagents and recursive adapter CLI launch are not portable substitutes.

Keep native agents distinct from registered headless worker dispatch; a restriction on one surface never silently extends to the other. Preserve model role, intensity, depth, required tools/tests, safety, and validation when falling back. Do not run drill automatically.

## Runtime Lifecycle

Claude hooks realize portable invariants for workflow signals, write/spec/core gates, memory, and design checks. Use explicit wrappers when a hook cannot be trusted. Main-session memory lifecycle and distillation do not run for workers. Session end never owns destructive worktree cleanup.

Use `statusline.sh` only for runtime status. Harness detail remains available through the adapter tools and docs. Runtime-owned credentials, sessions, logs, caches, databases, and config stay outside this repo.

## Context and Memory

Memory semantics belong to the acting agent. When prior context may materially help, choose a targeted query through `tools/memory/recall.sh`; retrieve full pending obligations before applying and consuming them.

Context pressure is orthogonal to quality and stage graph. Ordinary hook states stay silent. Static bytes, code lines, and directive counts are footprint measures, not token or billing savings. `core/ADAPTATION.md §6.1` owns budgets; real savings claims require paired production sessions.

## Response Policy

Portable behavior contract = `roles/response-policy.md`.

- **Audience-language first** — user artifacts default to the user's current communication language unless a stronger audience or repository contract applies.
- Keep responses concise and match promises with same-turn action.
- Verify before asserting and follow existing conventions.
- Ask only for genuinely non-obvious or destructive choices; proceed with the recommended reversible path when no answer is needed.
- In an active “do X” flow, implied records, validation, commit, and push follow without repeated confirmation.

Claude-specific realization: keep work grounded in current files, expose changes before committing, and commit/push validated harness changes.

## Compatibility Boundary

Codex and OpenCode files are sibling implementation references, never Claude bootstrap input. Portable meaning comes from `core/`, `capabilities/`, and `roles/`; map that meaning to Claude-native runtime surfaces.
