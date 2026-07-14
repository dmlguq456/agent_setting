# Inline implementation review

> reviewer: code-execute self-review fallback · independent QA: **not claimed** (depth 3 forbidden)

## Boundary review

- Source changes stay inside the plan's expected file/class ownership; specs, test logs, final report, runtime config, hooks.json, model/dispatch/QA contracts, and OpenCode utility projection were not changed.
- Production Codex paths import only `token_accounting` and canonical Phase 1 directive data. `offline-forecast-v1`, `token_experiment`, and `production_dynamic_enabled` are absent from `utilities/token-budget.py`, `userprompt-lifecycle.py`, `preflight.sh`, and `hooks.json`.
- The isolated CLI exposes only explicit replay/evaluate behavior, validates frozen code/fixture hashes, emits canonical JSON, keeps production false, and cannot return an adopted verdict.

## Correctness review

- Accounting reducer enforces `hook_invocations = zero_injections + emissions`; fixed zero reasons, exact inserted bytes, monotonic sample semantics, decrease/unavailable counters, and absent tokenizer estimate are covered by focused tests.
- Directory-wide bounded stale-safe lock, atomic replace, per-file/directory bounds, oldest-first prune, and content-free sha256 session paths are implemented fail-open.
- Evaluator recomputes each workload config fingerprint from all pairing fields, applies fixed exclusion priority, paired 10,000-sample bootstrap seed 20260713, ordered G1–G6 gates, both quality/delta comparisons, and exact bytes/emissions reporting.

## Findings

- No blocking implementation finding remains in the inline pass.
- Full Fleet, portable guard, adaptation boundary, manifest check, doctor, and independent thorough QA remain code-test obligations.
