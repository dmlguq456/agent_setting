# Token Self-Regulation Phase 2/3 — Verification Retry 2

## Verdict

`READY_FOR_CODE_REPORT`

The fresh separate depth-2 `code-test` retry restarted at matrix item 1 and
completed all 15 required items without a substantive implementation failure.
Source, spec, plan, checklist, implementation logs, pipeline summary, runtime
projection, and runtime configuration were not modified.

## Target and contracts

- Trigger: `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/plan.md`
- Component SoT: `spec/token-self-regulation/prd.md` v2,
  `experiment_contract.md` v1, `pipeline_state.yaml`, and component summary
- Runtime mode: Codex `code-test`, native `qa/test`, thorough, depth 2
- Executable tool contract: adapter-owned `verification-runner` available
- QA policy: independent relative to `code-execute`; no external adversary or
  depth-3 reviewer is claimed

The flat component-spec gate limitation remains: it models the unrelated root
PRD, while the actual component SoT was read and marked. The native
`apply_patch` target-inference limitation also reproduced when writing this
evidence; the explicit-preflight shell `apply_patch` fallback was used.

## Fresh matrix results

1. **AST — PASS.** All eight Python files from plan section 8 parsed.
2. **Focused Phase 2 — PASS.** 16 tests in 6.617s.
3. **Focused Phase 3 — PASS.** 8 tests in 2.427s.
4. **Fleet integration — PASS.** 214 tests in 13.002s.
5. **Public CLI behavior — PASS.** Replay/evaluate were each run twice with
   byte-identical output. Manifest SHA-256 was
   `5238ea5073cbebefaf0ef9fee9d09750775e0420ed96b5141839682d61942424`,
   replay SHA-256 was
   `6b4df8c857121dc93e31aefb71082ee81b2b876546ab26b5337d12cd9a771314`,
   and evaluator SHA-256 was
   `1ca0899497a4f5dab0c33781178a26e23431bcd21fc97b8871ee93d2e8128a96`.
   The 30 triplets were synthetic/non-evidentiary. Verdict remained
   `eligible_for_user_review`, adoption `pending_user_decision`, production
   false, bootstrap 10,000/20260713, bytes
   `{control:0,static:4620,dynamic:4620}`, emissions
   `{control:0,static:30,dynamic:30}`.
6. **Portable guards — PASS.** The one and only invocation returned
   `PASS=344 FAIL=0`. Current source creates a unique `$TMP`; fixed global
   runtime-projection/doctor/context captures are absent.
7. **Adaptation negative guard — PASS.** Negative cases passed, baseline was
   restored, and the final guard was green.
8. **Adaptation boundary — PASS.** Boundary checks passed; 56 documented
   Claude/model-reference warnings remained non-failing.
9. **Manifest freshness — PASS.** Manifest and delta baselines were current.
10. **Doctor — PASS.** Repository readiness checks were `ok`.
11. **Doctor runtime — PASS.** Runtime projection was `ok`.
12. **Runtime projection — PASS.** Installed wiring reported `status=ok`,
    hook trust `ok`, 27 projected skills/28 links and 9 agents/9 links.
13. **Diff whitespace — PASS.** `git diff --check` exited 0.
14. **Production isolation — PASS.** Four paths × three forbidden needles
    produced zero matches.
15. **Hash/parity/projection/defer — PASS.** Candidate code SHA-256
    `e9fb3cfed40f99953bdc4b75b57d95e42d79a571f311b525d8f5dbb698a0c5ae`
    and fixture-set SHA-256
    `e0158bb7f8e24f5f6fc2d40fea0d6b04f872f194dd61ff947eaa86e6b7ab959e`
    matched the manifest; all 35 Fleet files matched the Claude mirror; the
    Codex symlink resolved to the canonical CLI; OpenCode had no projection and
    all three adapter documents retained the explicit defer boundary.

## v2 assertion coverage

- **Phase 2/Phase 1:** focused and Fleet suites verified sha256/content-free
  state, exactly-once identity/all zero reasons, tight/critical inserted strings
  (154/165 UTF-8 bytes; transport newline excluded), monotonic/decrease/
  unavailable samples, absent token estimate, 8 KiB/file + 256 files + 2 MiB
  bounds, oldest-first pruning, atomic/concurrent updates, timeout exactly once,
  privacy, and fail-open behavior. Production transition/zero bytes remained
  stable; L2 stayed in `kv|json` and never entered hook output.
- **Phase 3:** tests and public CLI verified frozen pure
  `offline-forecast-v1`, directive IDs, deterministic replay, duplicate
  suppression/reopen, unknown no-early-emission, strict triplets/exclusions,
  n/strata, safety+required 100%, no hard regression, both quality LCBs, both
  paired observed-delta comparisons, 10,000/20260713 bootstrap, exact bytes/
  emissions, maximum eligible verdict, pending adoption, synthetic fixtures,
  and production false.
- **Isolation:** no production candidate import/activation/config mutation was
  found. Model, effort, intensity, dispatch/depth, QA, guards, pruning, RL,
  online fitting, and runtime-owned config were unchanged. Claude parity and
  Codex selective projection passed; OpenCode remains explicitly deferred.

## Verifier command-selection note

The initial item-15 script added an unnecessary requirement that every OpenCode
document separately contain both literal phase labels; a first narrow diagnostic
repeated an exact-phrase version. These two exits were verifier-selection errors,
not source/test failures or long-command reruns. The intended adapter-specific
assertions passed. `commands_retry2.log` preserves all exits.

## Runtime boundary

No runtime projection was installed/refreshed. Items 11–12 inspected the
currently installed main harness at `/home/Uihyeop/agent_setting` and wiring
under `/home/Uihyeop/.codex` read-only; they do not exercise the uninstalled
worktree diff.

`READY_FOR_CODE_REPORT`
