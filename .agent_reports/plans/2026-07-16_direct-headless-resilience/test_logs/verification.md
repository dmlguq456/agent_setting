# Direct Headless Resilience — verification

verdict: **PASS**
scope: SD-58, SD-59, SD-60 on broker-retired direct headless

## Focused acceptance

- `python3 -B utilities/dispatch_progress.test.py` — PASS, 10.
- `python3 -B utilities/stage_dispatch_capacity.test.py` — PASS, 6.
- `python3 -B utilities/dispatch_registry.test.py` — PASS, 8.
- `python3 -B utilities/stage_dispatch_fallback.test.py` — PASS, 7.
- `python3 -B utilities/dispatch_contract.test.py` — PASS, 10.
- `python3 -B utilities/nested_dispatch_eligibility.test.py` — PASS, 4.
- `python3 -B utilities/worker_dispatch_prompt.test.py` — PASS, 2.
- `python3 -B utilities/dispatch_adapters_v11.test.py` — PASS, 6.

The focused fixtures cover warning -> interrupt, deterministic progress reset,
speech-only negative evidence, PID reuse, native proof, capacity success and
second-failure descent, same/disallowed model rejection, exact per-attempt log
isolation, newest-attempt filtering, mixed reconciliation, idempotency,
concurrency, and namespace-local heartbeat classification.

## Adapter and liveness regression

- `bash utilities/dispatch-liveness.test.sh` — PASS, including exact live PID,
  exited PID, legacy transcript fallback, and namespace-local depth-2 heartbeat.
- Claude, Codex, and OpenCode `dispatch-headless.sd15.test.sh` — PASS.
  Capacity closure is exercised alongside existing rate/auth/usage behavior;
  prose describing capacity does not become a terminal capacity event.

## Fleet, parity, and boundaries

- `python3 -B -m unittest discover -s tools/fleet/tests -p 'test_*.py'` —
  PASS, 569 tests.
- `python3 -B tools/fleet/tests/test_mirror_parity.py` — PASS.
- `diff -qr tools/fleet adapters/claude/tools/fleet` — PASS.
- `bash hooks/portable-guards.test.sh` — PASS (`PASS=368 FAIL=0`).
- `bash tools/check-adaptation-boundary.sh` — PASS after cache cleanup.
- `git diff --check` — PASS.
- Python syntax/compile and shell syntax checks — PASS; no `__pycache__`
  remained at the boundary check.

## Independent verification

The separate verifier reported PASS with no blockers. Its five focused repros
closed:

1. relative/glob write scope and route-output progress signatures;
2. capacity prose false positive versus true plain/JSON terminal capacity;
3. delayed capacity exact-row closure and retry route;
4. superseded-attempt liveness filtering;
5. route-bound Codex depth-2 `.dispatch` write scope without nested network.

## Runtime smoke

The real recursive smoke is recorded in `test_logs/recursive-smoke.md`. It
proved direct Codex headless recursion and stage heartbeat emission. Its only
finding—namespace-local child PID visibility—was fixed afterward and covered by
Fleet, registry, liveness, and adapter tests before final integration.

Final verification verdict: **PASS**.
