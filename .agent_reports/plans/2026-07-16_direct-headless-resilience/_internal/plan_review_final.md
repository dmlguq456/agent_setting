# Final narrow plan review — direct-headless resilience

verdict: **PASS**

scope: final review of the amended implementation plan and refinement record against the blockers recorded by the fast and deep plan reviews. No source files were edited.

## Resolution check

- **SD-58 watchdog ownership and lifetime — resolved.** The public synchronous owner is `stage-dispatch-fallback.py --start` with injectable window/budget arguments. Observation continues after deterministic progress resets, uses two consecutive quiet windows, revalidates exact attempt/PID/start immediately before signal, persists idempotent state, closes only the exact attempt, and resumes the existing SD-50 iterator. Live PID identity is safety evidence; only deterministic progress fingerprints refresh the quiet counter.
- **Heartbeat semantics and single classifier — resolved.** Repeated phases are accepted only with a changed deterministic digest; unchanged/replayed evidence does not refresh time. Fleet, watchdog, liveness, and reconciliation are assigned to the shared F-25 attempt classifier, and concrete prompt/liveness consumers are named.
- **Native-subagent proof — resolved.** Capability support alone cannot pass the hop; exact row/PID/producer-owned artifact proof is required or the chain fails closed and descends.
- **SD-59 exactly-one capacity retry — resolved.** The plan defines adapter-paired alternative inputs, pins allowlisting/resolution to checked adapter role/model maps and tracked profiles, resolves to a comparable concrete model before launch, rejects partial/unproved/same/cooled selections, keeps selection outside wrappers, and uses locked canonical row evidence to prevent a second retry across reruns.
- **SD-60 current filtering and exact-death reconciliation — resolved.** Filters are applied before totals/decisions, mutation is dry-run unless explicitly applied, exact identity is re-read and reclassified under the SD-49 lock, and SD-29 gates remain authoritative.
- **`dead-stale-terminal` class separation — resolved.** It is now distinct from confirmed exact PID death and requires positive terminal proof: a valid SD-56 marker matching route id/hash/node/gate, naming an existing evidence artifact, with marker/evidence newer than the unterminated row. Newer transitions/process/activity, missing or invalid proof, clock ambiguity, exact-dead identity, and newer sibling attempts are explicit vetoes. Quiet time alone cannot authorize closure.
- **Runtime/topology and delivery boundaries — resolved.** No broker-like component is introduced; nonexistent Claude preflight projection is not required; live nested smoke and final commit remain depth-1-owner-only; QA is `thorough`; canonical artifacts and no-merge/no-push commit evidence are explicit.
- **Verification feasibility — resolved.** Focused SD-58/59/60 fixtures, dispatch regressions, full Fleet, mirror parity, portable guards, compile/syntax, adaptation boundary, owner-only direct-headless smoke, and final git checks are ordered sequentially.

## Final gate

The plan is sufficiently concrete for `code-execute`. Remaining implementation choices are local design details constrained by named interfaces, safety predicates, tests, and completion gates; no prior fast/deep review blocker remains open.
