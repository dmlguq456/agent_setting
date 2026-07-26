# Codex supervised parent lease + nested auth stabilization

## Route and scope

- Primary capability: `autopilot-code`, debug/standard, standard code QA.
- Secondary capability: `autopilot-spec`, update mode, because the accepted
  parent-liveness evidence contract changes SD-72/77/78.
- Spec significance: **SPEC-SIGNIFICANT** — an App Server supervised owner may
  prove liveness across PID namespaces with an attempt-scoped held lease; this
  is not permitted by the current PID-only wording.
- Source worktree: `/home/Uihyeop/agent_setting-wt/codex-supervised-parent-lease-auth`.
- Canonical artifacts remain under `/home/Uihyeop/agent_setting/.agent_reports`.
- Self-hosting exception: `STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification`.
  The registered depth-2 path under repair cannot own its own implementation
  stages until the fix has passed deterministic tests.

## Confirmed causes

1. The App Server tool sandbox cannot observe the outer owner/governor PID, so
   `attempt_process_quiescence` correctly returns
   `process-namespace-unverifiable`; the depth-2 parent gate incorrectly treats
   that as proof of death even while the supervisor is still active.
2. Codex auth eligibility accepts only output whose first non-whitespace text is
   `Logged in`. A harmless warning before the valid login line therefore makes
   repeated probes oscillate from supported to `auth-unavailable`.

## Implementation plan

1. Update the portable operations contract and stage-dispatch component PRD.
   Define a supervisor-held `flock-v1` liveness lease that is exact-attempt,
   canonical-registry-path bound, and never a launch authority or daemon.
2. Add shared lease validation/probing to `dispatch_contract.py`. PID evidence
   remains primary; a held lease is accepted only for an open
   `app-server-supervised` depth-1 owner when PID evidence is namespace-
   unverifiable. A missing, malformed, foreign, symlinked, or unlocked lease
   fails closed, and quiescent/PID-reuse evidence is never overridden.
3. Make the Codex App Server supervisor hold the exact lease for its full active
   lifetime. Seal the lease kind/path in the owner row and pass the path through
   the wrapper without exposing new authority.
4. Revalidate the same exact parent evidence before child spawn, after fenced
   spawn, and throughout a foreground-scoped wait so parent loss still tears
   down the direct child.
5. Make Codex login parsing line-oriented: require exit 0 and accept an exact
   nonempty line beginning `Logged in`, regardless of preceding warnings.
6. Add regression tests for held/released/foreign lease behavior, namespace
   fallback, pre/post-spawn parent loss, supervisor lifetime cleanup, and
   warning-prefixed auth output. Run focused suites, broad dispatch/liveness/
   harvest/adaptation checks, then one bounded real owner→`code-plan` launch and
   exact liveness/harvest verification.

## Completion criteria

- A supervised depth-1 owner remains an eligible exact live parent from its
  App Server tool PID namespace without weakening ordinary PID checks.
- Repeated Codex nested-auth probes remain `supported` when the CLI emits a
  warning followed by a valid login status.
- A real depth-2 `code-plan` start reports `child_spawned=1`.
- Parent and child liveness, completion delivery, exact harvest, and terminal
  reconciliation pass; unrelated hook-trust and OpenCode depth-2 support are
  unchanged.
