# Token Self-Regulation Phase 2/3 — Verification Retry 1

## Verdict

RETURN_TO_CODE_EXECUTE

The fresh separate depth-2 code-test retry restarted at matrix item 1 and
stopped at the first substantive failure, item 6
(hooks/portable-guards.test.sh). No source, plan, checklist, implementation
log, pipeline summary, runtime projection, or runtime configuration was changed.

## Target and contracts

- Trigger: .agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md
- Component SoT read: spec/token-self-regulation/prd.md v2,
  experiment_contract.md v1, pipeline_state.yaml, and component
  pipeline_summary.md
- Runtime mode: Codex code-test, native qa/test, thorough, depth 2
- Executable tool contract: adapter-owned verification-runner available
- QA policy: independent verification relative to code-execute; external
  adversary and depth-3 review are not claimed

The known flat component-spec gate limitation remains: it models only the flat,
unrelated root PRD. Actual component-SoT read evidence was completed and marked.
The native apply_patch target-inference limitation recorded by correction 01
also reproduced while writing this evidence; the explicit-preflight shell
apply_patch fallback was used without weakening the verdict.

## Fresh graduated results

1. Syntax — PASS. All eight Python implementation/test files from plan section
   8 parsed successfully.
2. Focused Phase 2 — PASS. 16 tests in 6.437s.
3. Focused Phase 3 — PASS. 8 tests in 2.283s.
4. Fleet integration — PASS. 214 tests in 12.944s.
5. Behavioral public CLI observation — PASS. Replay and evaluate were each run
   twice with byte-identical output. Replay SHA-256 was
   6b4df8c857121dc93e31aefb71082ee81b2b876546ab26b5337d12cd9a771314;
   evaluator SHA-256 was
   1ca0899497a4f5dab0c33781178a26e23431bcd21fc97b8871ee93d2e8128a96.
   The 30-triplet fixture was synthetic/non-evidentiary. Output remained capped
   at eligible_for_user_review, adoption remained pending_user_decision,
   production_dynamic_enabled=false, bootstrap remained 10,000 resamples with
   seed 20260713, bytes were {control:0,static:4620,dynamic:4620}, and emissions
   were {control:0,static:30,dynamic:30}.
6. Portable guards — FAIL after one 143-second invocation captured from the
   initial run. Final summary:

       BAD codex check-runtime-projection should reject miswired skill and agent links
       BAD codex doctor --runtime should include runtime projection validation
       PASS=342 FAIL=2
       status=failed
       exit_code=1

## First actionable failure

hooks/portable-guards.test.sh uses fixed global files such as
/tmp/codex_rp_bad.out and /tmp/codex_doctor_runtime.out for its runtime
projection assertions, even though it otherwise owns a per-run $TMP directory.
Immediately after this run, those diagnostic files contained
/home/Uihyeop/agent_setting-wt/language-neutrality as agent_home and as the
expected skill/agent target instead of this assigned
token-self-regulation-phase2-3 worktree. This is evidence of cross-worktree
temporary-output clobber during parallel guard execution and explains both
failed assertions. Code-execute should make these captures run-unique (prefer
the existing per-run $TMP) without weakening the runtime-projection or doctor
assertions, then request another fresh matrix retry.

Matrix items 7–15 were not executed because stop-on-first-substantive-failure
was mandatory. Their standalone adaptation/boundary/manifest/doctor/runtime,
diff, production-absence, hash/parity/symlink, and OpenCode-defer assertions are
therefore not current retry evidence.

## Assertion coverage at stop

- Phase 2 tests freshly covered sha256/content-free state, invocation identity,
  all fixed zero reasons, exact inserted bytes, monotonic/decrease/unavailable
  samples, absent token estimate, bounded oldest-first storage, concurrency,
  timeout exactly-once, privacy, and fail-open behavior.
- Phase 1 regression paths freshly preserved transition-only/zero behavior and
  L2 diagnostics limited to kv|json; hook output remains free of accounting
  diagnostics.
- Phase 3 tests and public CLI observation freshly covered frozen replay,
  directive IDs, duplicate suppression/reopen, unknown no-early-emission,
  strict pairing/exclusions, n/strata, required+safety/hard-regression gates,
  both quality LCBs, both 10,000-resample paired comparisons at seed 20260713,
  deterministic bytes, exact bytes/emissions, verdict cap, pending adoption,
  synthetic-only fixtures, and production false.
- Full explicit production dynamic-absence, manifest hash, canonical/Claude
  parity, Codex projection symlink, and OpenCode absence/defer evidence remains
  unverified in this retry because those matrix items follow the failed item.

## Runtime boundary

No runtime projection was installed or refreshed. Item 6 exercised temporary
fixture homes and was itself disrupted by cross-worktree fixed /tmp captures.
Matrix items 11–12, which would inspect installed main wiring read-only, were
not run. Nothing here claims that installed main wiring exercised the
uninstalled worktree diff. OpenCode Phase 2/3 remains explicitly deferred.
