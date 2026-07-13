# Token Self-Regulation — Final Report

## Outcome

Phase 0–1 is implemented on the dedicated `token-self-regulation` worktree branch.

- Session telemetry now separates active context occupancy from cumulative input/cache/output/reasoning/total counters.
- Codex exact-session rollout observation uses the native 12k reserve formula and event-time freshness.
- Fleet carries explicit cross-adapter fields while preserving legacy `Session.tokens` rendering behavior.
- A portable `token-budget.py` exposes `kv`, `json`, and transition-only `hook` outputs.
- Codex UserPromptSubmit emits at most one <=240-byte directive on tight/critical entry and remains silent for normal, unknown, repeated, degraded, or validated-native states.
- Token pressure cannot lower intensity, dispatch/depth, model role, required stages/tools/tests, safety, validation, input context, or guards.

## Verification

- 12 focused token-budget tests.
- 202 full Fleet tests.
- 343 portable guards, 0 failures.
- adaptation boundary, manifest, native skills/plugin/agents/modes, mirror parity, diff check, and repository doctor passed.
- Two independent read-only implementation reviews completed; all actionable findings were corrected and no P0/P1 remains.

## Runtime/install boundary

Repository readiness is green. The installed `$CODEX_HOME` projection still points to main rather than this feature worktree, so `doctor --runtime` correctly reports a projection mismatch before integration. No runtime projection, `config.toml`, credential, transcript, or session store was mutated.

## Deferred scope

- Phase 2: measured reinjection bytes/tokens, net savings, and cadence evaluation.
- Phase 3: dynamic-policy experiment and a separate adoption gate.

Implementation commit `0f8f52a` was pushed to `origin/token-self-regulation`. The branch is ready for main-session review and integration; this worktree does not self-merge.
