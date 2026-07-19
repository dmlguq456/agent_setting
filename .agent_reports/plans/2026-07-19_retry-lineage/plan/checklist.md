# SD-67 implementation checklist

Safety commit: `fb9a098f14f6e5f75a139dc4f5d0fda92904ed91`

Core-first commit: `92f25ea04121ada80d8fd50efba51b904b7cc4a5`

## Plan-stage evidence

- [x] Read governing PRD §13.9.1 SD-67 and §13.7 / SD-65.
- [x] Inspected guard validation, mutation classification, and first-parent helper.
- [x] Counted and inspected all 8 existing worker-route-guard tests.
- [x] Measured route validation and attempt-claim order in all three wrappers.
- [x] Selected `stage-dispatch-fallback.py::registry_rows` for parser reuse.
- [x] Recorded standard/code QA assurance and inline-review fallback.

## Execution

- [x] Re-read/mark and edit `core/OPERATIONS.md §5.10` first.
- [x] Commit core alone; record its hash above before adapter/Skill edits.
- [x] Implement mutation retry evidence and `--current-attempt` in the guard.
- [x] Propagate current attempt through all wrappers without moving claim order.
- [x] Replace Step 4 safety-commit restore wording and keep both references byte-identical.
- [x] Add SD-67 acceptance/exclusion tests while preserving the original 8.
- [x] Commit implementation only after core.

Derived implementation commit: `9b43d75468cdfb9a56260f8604eec30d3d6035d9`

## Acceptance mapping

- [x] A1 prior same-route/execute attempt + first-parent descendant passes.
- [x] A2 no prior attempt retains exact-match rejection.
- [x] A3 divergence and unavailable/unreadable registry fail closed.
- [x] A4 SD-65 downstream lineage and all original 8 tests remain green.
- [x] EX current attempt alone cannot self-authorize.

## Regression suite

- [x] `python3 utilities/worker_route_guard.test.py` — 13/13 OK
- [x] `python3 utilities/dispatch_contract.test.py` — 10/10 OK
- [x] `python3 utilities/dispatch_node.test.py` — 17/17 OK
- [x] Claude/Codex/OpenCode `dispatch-headless.sd15.test.sh` — PASS/PASS/PASS
- [x] Claude/Codex/OpenCode `dispatch-headless.sd45.test.py` — 9/9 OK each
- [x] `python3 utilities/stage_dispatch_fallback.test.py` — 8/8 OK
- [x] `bash utilities/dispatch-route.test.sh` — PASS
- [x] Python compilation, reference byte parity, wrapper semantic parity, `git diff --check` — all clean
- [x] Confirm out-of-scope surfaces remain unchanged — no `spec/**`/`capability-route.py`/SD-68/selector/permission-classifier diff

Full detail: `dev_logs/execute-claude.md`.
