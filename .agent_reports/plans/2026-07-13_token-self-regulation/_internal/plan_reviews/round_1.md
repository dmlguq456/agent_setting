# Plan Review — round 1

## Verdict

PASS WITH LOCKED SAFETY CONDITIONS.

## Independent findings incorporated

1. `intensity` and token pressure remain orthogonal; no model, role, stage, depth, QA, or required guard reduction.
2. The research phrase “tight -> dispatch suppression” is removed from the implementation policy.
3. Active context and cumulative session counters use separate fields; legacy `Session.tokens` is not a policy input.
4. Unsupported adapters remain 0-injection and do not claim automatic parity.
5. Native Codex rollout budget requires explicit validated opt-in because 0.144.1 rejects the documented config path.
6. Reinjection is band-transition-only with a hard byte cap.
7. Static `context-footprint.py` remains reserved for Phase 2 reinjection accounting.

## Residual risks to verify

- Hook state must be session-isolated and atomic enough for duplicate invocations.
- Exact rollout discovery must reject ambiguous matches.
- Decreasing cumulative counters must suppress policy injection rather than invent a corrected value.
- Full guard/mirror tests must confirm no projection drift.
