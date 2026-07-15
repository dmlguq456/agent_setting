# Final verification

Verdict: **PASS**. All six v10 acceptance criteria are covered.

## Commands and results

- `bash hooks/portable-guards.test.sh` via Codex verification runner — PASS, 359/359.
- `python3 tools/capability_topology.test.py` — PASS, 8 tests.
- `python3 utilities/capability_route.test.py` — PASS, 7 tests.
- `python3 utilities/worker_route_guard.test.py` — PASS, 3 tests.
- `python3 utilities/spec_transaction.test.py` — PASS, 2 tests.
- Each of `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py` — PASS, one independent fixture per adapter.
- `python3 tools/build-manifest.py --check` — PASS.
- `python3 tools/generate.py --check` — PASS, 10 projection groups current.
- `env -u AGENT_ARTIFACT_ROOT bash tools/generated-projections.test.sh` — PASS, including 29 figure-semantic regressions.
- `bash tools/routing-contract.test.sh` — PASS.
- `python3 tools/context-footprint.py --root . --skip-runtime --skip-hooks --strict` — PASS, no warnings; Codex bootstrap 7,972 bytes within 8,028-byte limit.
- `bash tools/check-adaptation-boundary.sh` — PASS (documented concrete-reference warning only).
- tracked→escalation census over core/adapters/capabilities/utilities/tools — PASS, zero matches.
- Python/shell syntax checks and `git diff --check` — PASS.

## Acceptance mapping

1. SD-44 independent tracking/escalation fields and route properties — PASS.
2. SD-44 tracked→escalation prose census — PASS, zero residual coupling.
3. SD-45 hash/scope/evidence/source-state refusal — PASS.
4. SD-45 three sibling adapter fixtures — PASS independently; native risk review PASS.
5. SD-46 invalid recipe and structured runtime guard failure — PASS.
6. SD-47 concurrent transaction produces BLOCKED then v1/v2 without duplicate snapshot; missing spec-touch is structured — PASS.

## Tool contracts

- `verification-runner`: supported and used for final executable gates.
- registered `headless-dispatch`: unavailable in this sandbox after runtime isolation because outbound Codex API access was denied. Failure evidence is under `_internal/failed-code-plan-*.json`; no headless QA claim is made.
