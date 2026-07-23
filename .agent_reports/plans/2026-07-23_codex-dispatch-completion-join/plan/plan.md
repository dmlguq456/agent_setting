# Codex registered-dispatch completion join

## Objective

Replace SD-14's model-driven wait loop for `standard+` Codex registered-headless owners with a runtime-owned completion join. Preserve Fleet registration, exact attempt identity, file-only stage handoff, checked fallback, and orphan reconciliation.

## Root-cause boundary

The defect is not child launch. It is ownership of the interval after a parent turn registers children and before those children become terminal. The LLM currently owns that interval through repeated `dispatch-wait`/terminal continuations. The corrected boundary is:

1. The owner model registers one or more children and yields the current turn.
2. A non-model supervisor joins every exact child attempt bound to the owner attempt.
3. The supervisor starts one continuation turn on the same Codex App Server thread with a bounded typed aggregate.
4. The model harvests exact attempts, advances the route, and emits the final three-line handoff only when no owned child remains unresolved.

## Work packages

### 1. Portable contract and stage-dispatch specification

- Supersede SD-14 same-turn model polling for runtimes with a checked completion supervisor.
- Define batch join, exact parent-attempt binding, bounded timeout/failure delivery, final-handoff gating, and a checked polling fallback.
- Keep post-exit orphan reconciliation as a safety net rather than the normal completion path.

### 2. Deterministic exact-child join

- Add a utility that snapshots and joins all current-contract children whose `parent_attempt_id` equals the owner attempt.
- Reuse canonical liveness/terminal classification without returning raw child logs.
- Return one bounded JSON receipt for ready, timeout, no-child, or contract-error states.
- Ignore unrelated parents and wait for every parallel child, not merely the first terminal child.

### 3. Codex App Server owner supervisor

- Add a stdio App Server client that owns one persistent Codex thread across stage completions.
- Normalize only the final completed turn into the existing Codex JSONL terminal contract; intermediate turn completions are supervisor events, not worker-terminal events.
- On intermediate completion, invoke the exact-child join outside the model and send one compact continuation input.
- Bound continuation count and join timeout; fail closed on protocol errors or malformed final handoff.

### 4. Wrapper and hook integration

- Select App Server supervision by default only for `standard+`, `worker_type=owner` Codex jobs after a runtime probe.
- Retain `codex exec` for stage workers, direct/quick one-shot workers, and a declared checked fallback when App Server is unavailable.
- Replace the prompt's polling instruction with a deterministic yield instruction.
- In supervised mode, deny model-issued `dispatch-wait`; allow exact harvest only after the supervisor's completion delivery.
- Surface the selected completion-delivery mode in wrapper/preflight output and documentation.

### 5. Verification and parity

- Unit-test App Server protocol sequencing, exactly-one final terminal event, batch join, parent isolation, timeout, and no raw child payload in continuation input.
- Replay the previously observed parent-waste classes and prove they remain denied.
- Run a live installed-Codex App Server smoke and a registered Codex owner/depth-2 fixture where feasible.
- Run the existing Claude/Codex wrapper, liveness, harvest, orphan, Fleet, projection, boundary, and portable-guard suites.
- Obtain an independent Claude review of the integrated diff; report reduced independence if the registered hop becomes unavailable.

### 6. Review-driven correction: batch registration phase

The first implementation made the supervised Codex guard too strict: once the
first child row became open it admitted only harvest, so a strong route could
not register the second independent depth-2 replica in the same batch. Refine
the contract as a two-set state machine owned by the supervisor:

- `delivered_attempt_ids ∩ open != ∅`: the model has received that batch and
  may issue only exact harvest for a delivered attempt.
- `open - delivered_attempt_ids != ∅` with no delivered attempt open: the
  model is still forming a new batch and may issue only another exact,
  parent-bound `dispatch-node --action start`.
- no open child: ordinary route/tool work may continue.

The supervisor writes this bounded state atomically outside the model loop and
removes it on exit. Codex reads it from its native PreToolUse bridge. Claude
receives a command-scoped PreToolUse hook through the verified `--settings`
surface, so the enforcement does not depend on mutating the user's runtime
settings. Also remove the duplicate final Codex `agent_message` and scope
terminal diagnostics to the last supervised turn boundary.

## Non-goals

- Reintroducing the retired launch broker, request spool, lease, or fencing system.
- Replacing registered headless work with native subagents.
- Editing `$CODEX_HOME/config.toml`, credentials, runtime sessions, or caches.
- Claiming that arbitrary detached stdout wakes an already completed interactive TUI turn.

## Acceptance criteria

1. During a simulated child runtime window, the parent App Server trace contains no `turn/start`, model event, or tool event.
2. Two exact depth-2 children can be open concurrently; continuation occurs only after both are terminal-ready.
3. Exactly one compact continuation is emitted per joined child batch and exactly one final `turn.completed` is written to the worker JSONL.
4. Unrelated, stale, malformed, or foreign-parent rows cannot wake the owner.
5. Timeout and protocol failure produce typed failure evidence and leave orphan reconciliation able to close exact descendants.
6. Existing terminal inspection and harvest consume the supervised log without compatibility changes to the three-line handoff.
7. App Server absence is reported as a checked polling fallback; it is never called parity.
8. Codex and Claude registered workers remain Fleet-visible with unchanged attempt identity and artifact boundaries.
9. After the first sibling opens, a second exact sibling dispatch is allowed,
   while source inspection, waits, and unrelated tools remain denied.
10. After a typed receipt, an unharvested delivered attempt admits exact
    harvest only; after closure, the next batch can again register multiple
    siblings.
11. Claude and Codex enforce the same phase rule without editing user-owned
    runtime configuration.
