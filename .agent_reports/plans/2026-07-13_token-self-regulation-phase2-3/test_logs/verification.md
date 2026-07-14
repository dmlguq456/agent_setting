# Token Self-Regulation Phase 2/3 — Verification

## Verdict

`RETURN_TO_CODE_EXECUTE`

The separate depth-2 `code-test` pass stopped at the first substantive failure,
required matrix item 6 (`hooks/portable-guards.test.sh`). Source, plan,
checklist, implementation logs, pipeline summary, and runtime configuration were
not modified.

## Target and contracts

- Trigger: `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md`
- Component SoT read: `spec/token-self-regulation/prd.md` v2,
  `experiment_contract.md` v1, `pipeline_state.yaml`, and `pipeline_summary.md`
- Runtime mode: Codex `code-test`, native `qa/test`, thorough, depth 2
- Executable tool contract: adapter-owned `verification-runner` available
- QA policy: this is independent verification relative to `code-execute`; no
  external adversary or depth-3 reviewer is claimed

The known flat spec gate limitation remains: the flat PRD gate models the
unrelated root PRD, while actual component-SoT read evidence was completed and
marked directly.

## Graduated results

1. Syntax — PASS. AST parsed all eight Python implementation/test files from
   plan section 8.
2. Focused Phase 2 — PASS. 16 tests in 6.537s.
3. Focused Phase 3 — PASS. 8 tests in 2.384s.
4. Fleet integration — PASS. 214 tests in 12.187s.
5. Behavioral CLI observation — PASS. Public `replay` and `evaluate` were each
   executed twice with byte-identical output. Replay SHA-256 was
   `6b4df8c857121dc93e31aefb71082ee81b2b876546ab26b5337d12cd9a771314`;
   evaluator SHA-256 was
   `1ca0899497a4f5dab0c33781178a26e23431bcd21fc97b8871ee93d2e8128a96`.
   The transient 30-triplet input contained synthetic hashes/IDs only. Output
   reported `eligible_for_user_review`, `pending_user_decision`,
   `production_dynamic_enabled=false`, 10,000 resamples with seed 20260713,
   exact bytes `{control:0,static:4620,dynamic:4620}`, and emissions
   `{control:0,static:30,dynamic:30}`. Replay fixtures remained explicitly
   `synthetic_non_evidentiary=true`.
6. Portable guards — FAIL. Deterministic diagnostic rerun reported:

   ```text
   BAD codex doctor --runtime should include runtime projection validation
   BAD codex doctor --runtime-strict should require and accept complete hook trust
   PASS=342 FAIL=2
   status=failed
   exit_code=1
   ```

## First actionable failure

The failing guard's captured doctor outputs both contained:

```text
check=native-subagents:ok
check=token-budget-experiment:ok
check=adaptation-boundary:failed
check=runtime-projection:ok
status=failed
```

Therefore the runtime-projection checks themselves were `ok`, but doctor could
not return overall `status=ok` because the repository adaptation-boundary check
failed. `code-execute` must diagnose and repair that boundary failure before
verification resumes. This pass did not run matrix items 7–15 after the stop.

## Assertion coverage at stop

- Phase 2 focused tests covered exact accounting identity/reasons/bytes,
  monotonic/decrease/unavailable samples, content-free hashed state, bounded
  oldest-first pruning, concurrency, timeout exactly-once, fail-open behavior,
  absent token estimate, and read-only L2 diagnostics.
- Phase 1 regression tests preserved transition/zero behavior and hook output
  byte expectations.
- Phase 3 focused tests and public CLI observation covered frozen replay,
  duplicate suppression/reopen, unknown no-early-emission, exclusion priority,
  n/strata gates, safety/quality/both delta gates, deterministic output, verdict
  cap, pending adoption, and production false.
- Full production-absence scan, manifest/parity/projection/OpenCode-defer checks,
  standalone adaptation guards, manifest check, repository doctor runs, installed
  runtime checks, and `git diff --check` remain unverified in this pass because
  stop-on-failure was mandatory.

## Runtime boundary

No runtime projection was installed or refreshed. The failed portable-guard
assertions used their temporary runtime fixture; they do not prove that the
uninstalled worktree diff is active in the currently installed main checkout.
