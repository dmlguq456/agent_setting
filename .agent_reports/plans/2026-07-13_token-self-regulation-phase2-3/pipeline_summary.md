# Pipeline Summary — Token Self-Regulation Phase 2/3

## Verdict

`within-spec`: Phase 2/3 implemented. Phase 1 output and zero paths are preserved; production dynamic behavior is absent; adoption remains pending. The maximum evidence verdict is `eligible_for_user_review`, not production adoption.

## Canonical stage order

1. `token-self-regulation-phase23-code-r2-plan`
2. `token-self-regulation-phase23-code-r2-execute`
3. `token-self-regulation-phase23-code-r2-test`
4. `token-self-regulation-phase23-code-r2-execute-fix1`
5. `token-self-regulation-phase23-code-r2-test-retry1`
6. `token-self-regulation-phase23-code-r2-execute-fix2`
7. `token-self-regulation-phase23-code-r2-test-retry2`
8. `token-self-regulation-phase23-code-r2-report`

## Changed files from `git status --short --untracked-files=all`

Portable core/invariants:

- `core/ADAPTATION_INVENTORY.md`
- `core/CONVENTIONS.md`
- `tools/fleet/token_budget.py`
- `tools/fleet/token_accounting.py`
- `tools/fleet/token_experiment.py`
- `tools/fleet/tests/test_token_budget.py`
- `tools/fleet/tests/test_token_experiment.py`
- `tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json}`
- `utilities/token-budget.py`
- `utilities/token-budget-experiment.py`

Fleet Phase 2/3 and tests:

- `tools/fleet/tests/test_token_budget.py`, `tools/fleet/tests/test_token_experiment.py`
- `tools/fleet/token_budget.py`, `tools/fleet/token_accounting.py`, `tools/fleet/token_experiment.py`
- the three `tools/fleet/tests/fixtures/token_experiment/*` fixtures above

Utilities:

- `utilities/token-budget.py`
- `utilities/token-budget-experiment.py`

Codex realization:

- `adapters/codex/ADAPTATION.md`
- `adapters/codex/AGENTS.md`
- `adapters/codex/README.md`
- `adapters/codex/bin/preflight.sh`
- `adapters/codex/hooks/userprompt-lifecycle.py`
- `adapters/codex/utilities/token-budget-experiment.py`

Claude mirrors:

- `adapters/claude/tools/fleet/token_budget.py`
- `adapters/claude/tools/fleet/token_accounting.py`
- `adapters/claude/tools/fleet/token_experiment.py`
- `adapters/claude/tools/fleet/tests/test_token_budget.py`
- `adapters/claude/tools/fleet/tests/test_token_experiment.py`
- `adapters/claude/tools/fleet/tests/fixtures/token_experiment/{manifest.json,replay.json,replay_expected.json}`
- `adapters/claude/utilities/token-budget-experiment.py`

OpenCode defer and guards/manifest:

- `adapters/opencode/ADAPTATION.md`
- `adapters/opencode/AGENTS.md`
- `adapters/opencode/README.md`
- `hooks/portable-guards.test.sh`
- `tools/check-adaptation-boundary.sh`

Report artifacts already present and consumed:

- `plan.md`, `checklist.md`
- `dev_logs/implementation.md`, `dev_logs/correction_01.md`, `dev_logs/correction_02.md`
- `_internal/dev_reviews/implementation_review.md`, `correction_01.md`, `correction_02.md`
- `_internal/plan_reviews/round_1.md`
- `test_logs/commands*.log`, `test_logs/verification*.md`
- `_internal/test_reviews/thorough_review*.md`
- this `pipeline_summary.md` and `final_report.md`

The worktree snapshot was dirty with 17 tracked and 12 untracked changes before report creation; no source or evidence file was omitted from this grouping. The two report files are the only files owned by this stage.

## Retry 2 evidence

All commands ran through `$AGENT_HOME/adapters/codex/bin/preflight.sh verification-runner` unless noted. The fresh matrix restarted at item 1:

- AST parse: PASS, 8 Python files.
- `python3 -m unittest -v tools.fleet.tests.test_token_budget`: PASS, 16 tests.
- `python3 -m unittest -v tools.fleet.tests.test_token_experiment`: PASS, 8 tests.
- `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`: PASS, 214 tests.
- Read-only replay/evaluate twice: PASS, byte-identical. Manifest SHA-256 `5238ea5073cbebefaf0ef9fee9d09750775e0420ed96b5141839682d61942424`; replay `6b4df8c857121dc93e31aefb71082ee81b2b876546ab26b5337d12cd9a771314`; evaluate `1ca0899497a4f5dab0c33781178a26e23431bcd21fc97b8871ee93d2e8128a96`.
- `bash hooks/portable-guards.test.sh`: PASS, `PASS=344 FAIL=0`; unique cycle-local `$TMP`, fixed global captures `0`.
- `bash tools/adaptation-guard.test.sh`: PASS; negative cases passed and baseline restored.
- `bash tools/check-adaptation-boundary.sh`: PASS; 56 documented warnings remain non-failing.
- `python3 tools/build-manifest.py --check`: PASS, manifest current.
- `preflight.sh doctor`: PASS.
- `preflight.sh doctor --runtime`: PASS, runtime projection included.
- `preflight.sh runtime-projection`: PASS, installed wiring only: `status=ok`, hook trust `ok`, `session_end=stop-alias`, 27 projected/28 linked skills and 9/9 agents.
- `git diff --check`: PASS.
- production dynamic absence scan: PASS, 4 paths × 3 needles, `matches=0`, `production_dynamic_absent=1`.
- item 15 intended contract: PASS: candidate SHA-256 `e9fb3cfed40f99953bdc4b75b57d95e42d79a571f311b525d8f5dbb698a0c5ae`, fixture-set SHA-256 `e0158bb7f8e24f5f6fc2d40fea0d6b04f872f194dd61ff947eaa86e6b7ab959e`, 35-file Fleet/Claude parity `1`, Codex symlink correct, OpenCode projection absent and defer docs `3/3`.

Behavioral output was `complete_triplets=30`, `bootstrap_resamples=10000`, `bootstrap_seed=20260713`, `directive_utf8_bytes_by_arm=control:0,static:4620,dynamic:4620`, and `emissions_by_arm=control:0,static:30,dynamic:30`. Fixtures and triplets are synthetic/non-evidentiary.

Item 15 recorded two non-substantive verifier assertion-selection exits before the narrow contract check passed: the first script over-required literal Phase 2/3 strings in every OpenCode document, and diagnostic-a repeated that mistake. These are not source/test failures, and the intended adapter-specific assertions passed.

## Main integration hardening and final evidence

Main performed a boundary-coupled hardening pass after the registered stages and
then obtained an independent read-only review. The review found and drove fixes
for duplicate workload-id sample inflation, subprocess spawn-error accounting,
raw diagnostic session ids, impossible directive byte/provenance inputs, and an
extra aggregate field. Independent re-review returned `PASS` with no
blocking/high/medium findings.

Fresh post-fix evidence:

- AST: 8 files; Phase 2: 21; Phase 3: 10; Fleet: 221 — all pass.
- Portable guards: `PASS=344 FAIL=0` in an isolated run with both normal
  main and feature log roots writable.
- Adaptation negative guard: pass with baseline restored.
- Adaptation boundary: pass with 56 documented non-failing references.
- Manifest, repository doctor, diff check, production dynamic absence: pass.
- Candidate SHA-256:
  `11288b737241598dcf585eb762cfc033f3cbcca70eee6ff583cb6065f6de3606`.
- Canonical/Claude mirror parity: 9/9; Codex symlink and OpenCode defer: pass.

Two initial portable attempts were contaminated by other worktrees' fixed
`/tmp` captures. A later isolated 343/344 run exposed only an isolation
`EROFS` on the normal Claude main-log fallback; binding that expected root
writable produced the final clean 344/344 result.

## Limitations and unsupported contracts

- The flat component-spec gate models only an unrelated flat PRD. Actual component SoT read evidence (`.agent_reports/spec/token-self-regulation/{prd.md,experiment_contract.md,pipeline_state.yaml}`) was used and marked; flat approval is not claimed as component approval.
- Native `apply_patch` target inference required the explicit-preflight shell `apply_patch` fallback; no assertion was weakened.
- The initial test boundary-cache issue and cross-worktree fixed `/tmp` capture issue were corrected and independently retested.
- `thorough` policy allows 2 deep + 2 fast reviewers, but this depth-2 stage cannot dispatch forbidden depth 3; inline fallback reviews are not claimed as independent QA. The separate code-test retry is independent relative to code-execute.
- OpenCode Phase 2/3 realization is explicitly deferred.
- Fixtures and synthetic 30 triplets are not real `n>=30` experiment evidence. Adoption is `pending_user_decision`; maximum verdict remains `eligible_for_user_review`.
- No runtime-owned `config.toml` mutation, commit, push, merge, or worktree cleanup occurred.

## Next main action

The main orchestrator should commit and push intentionally, merge, refresh and
strictly validate runtime projection after integration, then clean the
worktree. Real Phase 3 paired evidence remains a separate future run.
