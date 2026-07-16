# Deep plan review — direct headless resilience

verdict: **FAIL**

The plan is correctly ordered SD-58 → SD-59 → SD-60, preserves the v15 direct-launch/no-broker boundary, keeps wrapper model selection out of wrappers, names the canonical/Claude Fleet mirror, and requires locked revalidation before reconciliation. The following gaps prevent `ready-for-execute`:

1. **SD-58 has no closed watchdog call path.** Current `stage-dispatch-fallback.py` returns after the wrapper's short early-death watch, while the launched child continues detached. The plan adds a “watchdog operation” but does not identify who invokes and polls it for both no-progress windows, how that current-turn loop returns the exact interrupted attempt to the existing SD-50 iterator, or how concurrent conductor reruns avoid duplicate interrupt/fallback. Define one bounded conductor/preflight command with exact input/output and lock/idempotency semantics. Also separate the shared classifier's process-existence verdict from its progress fingerprint: a live exact PID is interrupt-safety evidence, not progress and must not reset the watchdog.

2. **SD-59 cannot yet prove a different allowed model across adapters.** Current fallback route candidates carry harness/transport eligibility, not model allowlists; `stage-dispatch-fallback.py` always passes `--model-role`; and wrappers require paired runtime settings (`model+reasoning`, `model+effort`, or `model+variant`). Current inheritance records only `model=inherit`, so it cannot prove resolution away from a cooled concrete model. Specify the orchestrator-owned selection schema/CLI for each adapter, the authoritative allow/role-map check, pre-launch resolution to a comparable concrete identity (or fail closed), and persisted cooldown/retry fields read under the SD-49 lock. Without that, “exactly one alternative” and same-model count zero are not implementable assertions.

3. **SD-60 leaves stale-row closure underdefined.** “completion/age conditions prove” and a `dead-stale`-style note are not a deterministic safety predicate. State the exact required conjunction (newest exact attempt, classifier result, completion-marker/terminal evidence, age source/threshold, route identity, and SD-29 vetoes), and require the same row version to be re-read under lock. Age alone must never close a live or weak-identity row. Reusing `worktree-cleanup.evaluate()` should preserve all its gates (lock, dirty/operation state, merge ancestry, pushed integration ref, process scan), not only the merged test.

4. **Surface scope needs one correction.** There is no `adapters/claude/bin/preflight.sh` in current source. Name the actual Claude portable surface (or explicitly mark it not applicable) instead of requiring an undefined sibling preflight projection.

No broker, spool, socket, resident watcher, daemon, lease, or supervisor is proposed; that boundary passes. Revise the four items above, then the plan is feasible for execution.
