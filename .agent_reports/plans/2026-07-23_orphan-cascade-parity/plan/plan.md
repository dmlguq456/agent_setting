# Orphan-free registered headless parity

## Objective

Prevent a dead dispatch-depth-1 conductor from leaving a live or stale-open
dispatch-depth-2 attempt, while keeping exact-attempt safety and applying the
same harness-owned lifecycle contract to Codex and Claude Code wrappers.

## Incident baseline

- `codex-headless-context-parity-owner` ended without `turn.completed` while
  `codex-headless-context-parity-plan-refine` was foreground-scoped.
- The post-exit watcher closed only the owner as `dead-parent-orphaned`.
- The child row remained open until a depth-0 exact-process audit manually
  closed it as `dead-parent-terminated`.
- Current SD-64/71 explicitly says detection only and forbids child closure;
  the observed Fleet orphan was therefore contract-compliant, not a display bug.

## Contract change

1. A registered stage attempt is sealed to the one live
   `parent_attempt_id`; a reused parent slug never grants teardown authority.
   Missing, dead, or ambiguous parent identity prevents both row creation and
   process spawn.
2. After the child row is claimed, the final parent identity check, child
   spawn, and child PID/start/PGID publication occur while holding the
   canonical jobs lock. The only observable outcomes are no child process or
   a fully attributable process group. Foreground supervision then observes
   the depth-1 attempt row's exact PID/start identity and terminates that group
   when the parent identity disappears. The detached owner watcher is the
   SIGKILL/backstop path; a foreground-scoped depth-1 without a watcher remains
   an explicit depth-0 residual-risk surface.
3. The detached owner watcher performs one exact, bounded cascade reconcile:
   terminal evidence wins; host-visible live child groups are TERM/KILL reaped
   only after PID/start/PGID revalidation immediately before each signal;
   namespace-local or already-gone rows are closed only with explicit
   parent-death evidence. After teardown, the child is classified again under
   the registry lock so a racing completion marker or typed terminal handoff
   wins over cascade closure.
4. PID reuse never grants signal authority: a start-tick mismatch leaves the
   replacement process untouched and closes only the exact recorded attempt as
   `dead-parent-exited`. Route conflict, missing live identity,
   non-group-leader targets, namespace-local rows without an outer identity,
   and unverifiable legacy live rows fail closed and remain visible for
   depth-0 handling. A PID-less exact-bound registered/launch-claimed row is
   safe to close as `dead-parent-exited`, because the atomic publication
   contract proves that no process was spawned.
5. No replacement conductor, retry, successor launch, or route advance is
   automatic.
6. The closed cascade vocabulary is finite: `dead-parent-terminated` for an
   exact group that required a signal, `dead-parent-exited` when the exact
   process was already gone or never spawned, and `dead-parent-scope-lost`
   when a recorded outer namespace identity disappeared with the parent.
   Codex `turn.completed` and successful Claude stream-json `result` envelopes
   are both parsed before applying these notes; a Claude runtime-error result
   cannot promote a handoff-looking payload.

## Implementation scope

- `core/OPERATIONS.md`
- `.agent_reports/spec/stage-dispatch/{prd.md,pipeline_state.yaml,pipeline_summary.md}`
- shared lifecycle/registry/watcher utilities
- Codex and Claude registered-headless wrappers
- deterministic parent-death, PID-reuse, same-slug retry, live-child,
  namespace-local, terminal-race, and cross-adapter conformance tests

Fleet rendering, native subagents, Claude agent teams/agent view, runtime
credentials/config, and unrelated open jobs are excluded.

## Verification

- Unit tests for exact parent resolution and bounded process-group teardown.
- Watcher regression proving owner and child rows both reach terminal state,
  sibling/unrelated attempts stay byte-identical, and a second run is idempotent.
- Wrapper matrix proving Codex and Claude both bind foreground children to the
  parent attempt and emit the same closed lifecycle vocabulary.
- Terminal-envelope fixtures proving Codex `turn.completed` and Claude
  stream-json `result` PASS/FAIL/BLOCKED evidence outranks cascade notes.
- Race and identity fixtures covering same-slug replacement owners, completion
  markers written around teardown, non-group leaders, dead group leaders,
  escaped descendants, and concurrent depth-0 reconcile.
- Real local `codex exec --json` and `claude -p --output-format stream-json`
  probes for the documented terminal event envelope, without claiming either
  runtime natively owns the harness registry.
- Existing dispatch, liveness, wait, harvest, route, Fleet, adaptation-boundary,
  and runtime-projection checks, including Codex-side liveness and harvest of a
  Claude terminal result.

## Completion

The cycle passes when every recorded process group whose leader identity can
be revalidated converges without an open direct child attempt or live exact
group, while unverifiable/non-group/escaped cases remain visibly fail-closed.
Both runtime wrappers must share the contract, all scoped regressions must
pass, and the integrated branch must be verified and pushed.
