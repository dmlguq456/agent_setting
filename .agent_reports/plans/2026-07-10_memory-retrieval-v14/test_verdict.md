# Test Verdict — Memory Retrieval v14

## Verdict
GREEN with pre-existing repository baseline notes.

## Focused Evidence
- `tools/memory/mem_retrieval_v14.test.sh`: PASS 16 / FAIL 0.
- `hooks/mem-recall-inject.test.sh`: PASS 18 / FAIL 0.
- `tools/memory/mem_cluster_e.test.sh`: PASS 31 / FAIL 0.
- `tools/memory/mem_cluster_e_gamma.test.sh`: PASS 40 / FAIL 0.
- `tools/memory/inject.test.sh`: PASS 21 / FAIL 0.
- `hooks/mem-distill-dispatch.test.sh`: PASS 36 / FAIL 0.
- Compile/syntax, generated agent checks, manifest, `git diff --check`: pass.
- Auto-recall engine, live store, 20 warm runs: median 46.91 ms, p95 49.00 ms, max 53.21 ms.

## Adversarial Review
The first pass reproduced six issues: cross-project dedup/upsert, destructive TOCTOU, expired pending invisibility, legacy restore quarantine loss, tracked/untracked gate drift, and incomplete consume workflow. A second pass found session-ID loss in Codex/OpenCode bridges and missing pending markers in recall output. All eight were fixed and re-reviewed; no P1/P2 remained.

## Baseline Notes
- Full portable guards: PASS 312 / FAIL 11. Failures are the existing dispatch register/harvest, shell liveness parity, and runtime doctor fixtures; none touch memory retrieval.
- Adaptation boundary: the existing missing Claude fleet projections `test_f15_rows.py` and `test_f14_title.py`; no new boundary failure.
- Drill was not run because it can launch paid headless sessions; `preflight.sh loop-info drill` remains the explicit path.
