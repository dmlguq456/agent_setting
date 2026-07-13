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

## Ponytail synthesis

The integration keeps Ponytail's useful idea — spend fewer tokens when work can
be expressed more compactly — but narrows it to an observable output-response
axis:

| Ponytail idea retained | Harness realization |
|---|---|
| Budget-aware self-regulation | Exact-session active-context pressure with deterministic normal/tight/critical bands |
| Be concise under pressure | Tight/critical transitions request concise user-facing output and defer only unrequested optional extras |
| Avoid waste | Normal, unknown, native-owned, and repeated bands inject zero prompt bytes |
| Know when not to be lazy | Required implementation, tools, tests, QA, safety, security, validation, error handling, accessibility, and input context are invariant |

The ambiguous or unsafe parts were excluded:

- “be lazy” cannot lower intensity, model effort, dispatch/depth, stage topology,
  reviewer budget, or definition of done;
- dispatch suppression from the research sketch was rejected because it conflicts
  with the standard+ execution contract;
- input pruning, transcript compression, and context deletion remain off;
- per-payload percentages are not presented as session savings: active context and
  cumulative session counters are explicit separate signals;
- repeated budget-rule reinjection is replaced by one <=240-byte line only on a
  verified band transition;
- missing, stale, malformed, ambiguous, or decreasing signals fail open instead of
  inventing a budget estimate;
- native rollout-budget support is never auto-enabled and runtime-owned config is
  never edited by this policy.

## Runtime/install boundary

Repository readiness is green. After fast-forward integration, the installed
`$CODEX_HOME` projection was refreshed from main with native skill discovery.
`runtime-projection --require-hook-trust` now passes, including `hooks-json:ok`
and hook trust. Runtime-owned `config.toml`, credentials, transcripts, and
session stores were not modified.

## Deferred scope

- Phase 2: measured reinjection bytes/tokens, net savings, and cadence evaluation.
- Phase 3: dynamic-policy experiment and a separate adoption gate.

Implementation commit `0f8f52a` and handoff commit `489fdae` were fast-forwarded
to main and pushed to `origin/main`.
