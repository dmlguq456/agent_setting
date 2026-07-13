# Implementation Metrics — token-self-regulation

## Routing

- capability: autopilot-code
- mode: dev/refactor (portable)
- intensity: thorough
- derived QA policy: 2 deep + 2 fast reviewer upper bound for selected passes
- stage graph: code-plan > code-execute > code-test > code-report
- spec significance: SPEC-SIGNIFICANT

## Dispatch fallback

- required default: standard+ headless stage dispatch
- observed blocker: `hooks-json:failed reason=not-harness-hook-projection`
- registry writes: none
- fallback: manual file-owned stages in dedicated worktree
- completeness claim: manual fallback only, not independent headless stage parity

## Separability judgment

The telemetry schema, parser, collectors, CLI, hook, and invariant docs share field names and threshold semantics; splitting write ownership across concurrent workers would create boundary-coupled edits and mirror drift. Read-only surface/risk reviews were delegated in parallel, while all source mutation remains one serial implementation path in this worktree. This is the SD-17 non-separable exception; no stage session re-dispatch is attempted after the failed headless gate.

## Review evidence

- surface reviewer: recommended shared parser, explicit Fleet fields, transition-only hook, mirror parity.
- risk reviewer: required intensity/safety/dispatch invariants and reported native 0.144.1 config-probe contradiction.

## Token policy budget

- normal/unknown/native/same-band hook output: 0 bytes
- tight/critical transition: <=240 UTF-8 bytes
- Phase 2 cost/saving claim: none
