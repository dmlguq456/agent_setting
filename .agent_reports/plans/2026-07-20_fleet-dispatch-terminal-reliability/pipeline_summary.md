# Pipeline Summary

## Result

The dispatch/Fleet failure path now terminates by exact attempt identity. A
Codex `turn.completed` handoff with `BLOCKED` or `FAIL` closes the registered
row; the reported bwrap `.codex` failure is typed `dead-sandbox-init`.
Namespace-local rows cannot borrow another session's cwd-wide transcript to
remain working, and a terminal watchdog observation outranks old heartbeat and
PID evidence.

Invalid worktree `.codex` file or symlink shapes are rejected before registry
creation whenever the inner Codex sandbox is enabled. Dispatch contract v3
also rejects runtime-surface labels such as `codex-exec-headless` as transport
values; `headless` and `interactive` are the canonical vocabulary.

Fallback now treats unproven `process-exited` as a failure and keeps inline
execution on the original route/node/completion gate. Fleet ordinary Codex
sessions use validated `task_started`, `task_complete`, and `turn_aborted`
lifecycle events before mtime, so a waiting TUI becomes idle immediately.

The prior depth-2 orphan-visibility fix existed only in the Claude Fleet mirror.
It was restored to the canonical `tools/fleet` implementation and parity is
green.

## Evidence

- The real incident log
  `agent-home-design-refs.att-06d24bdd7b0eb72a0690af78d61bb24978f9453e7cc0152a.codex.jsonl`
  was parsed as `dead-sandbox-init`.
- The regression fixture proves an exact namespace-local attempt closes with no
  watchdog and no completion marker, and Codex liveness returns `EXITED`, never
  `ALIVE`.
- The tracked `.codex` file fixture exits 65, emits
  `invalid-worktree-codex-mount-target`, reports `child_spawned=0`, and creates
  no jobs registry.
- Existing foreground completion-marker race and SD-15 limit-death suites pass.
- Fleet canonical full suite: 718 tests passed.
- Fleet Claude-mirror focused suite: 154 tests passed.
- Dispatch route/contract, lifecycle, fallback, registry, and adapter groups:
  151 tests passed.
- Live Fleet `--once`, adaptation-boundary, runtime projection, and runtime
  doctor checks passed.

## Scope Notes

The Herdr/delegation investigation reinforced the separation between
registered dispatch state and Codex session/native activity. This change uses
jobs/watchdog/exact logs for registered attempts and rollout task lifecycle for
interactive session activity. Cross-capability DAG/process-view work remains
outside this cycle because it already has a separate owner.
