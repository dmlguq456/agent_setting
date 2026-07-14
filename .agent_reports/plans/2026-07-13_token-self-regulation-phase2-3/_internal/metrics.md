# Implementation Metrics — Token Self-Regulation Phase 2/3

## Routing

- capability/owner: `code-plan` / `autopilot-code`
- mode/intensity/depth: `dev/refactor` / `thorough` / `2`
- parent/session: `token-self-regulation-phase23-code-r2` / `phase23-main-20260713`
- graph: `code-plan > code-execute > code-test > code-report`
- spec significance: `within-spec`
- branch/worktree: `token-self-regulation-phase2-3` / dedicated sibling

## Bootstrap/runtime snapshot

- workflow tracked; git operation none; tracked dirty 0; initial untracked 1; ahead/behind 0/0; branch_done signal 1
- Codex `0.144.3`; hooks and multi-agent stable/enabled
- rollout_budget/runtime_metrics/token_budget under-development/false
- installed projection status/hooks-json/hook-trust ok; no mutation from worktree
- strict-config feature probe unavailable because `codex features` rejects `--strict-config`; native activation remains disallowed

## Spec evidence and flat-gate gap

- flat gate read: `.agent_reports/spec/prd.md` (Unified Memory System, unrelated)
- actual component read: `.agent_reports/spec/token-self-regulation/{prd.md,experiment_contract.md,pipeline_state.yaml}`
- component read-marker command ran, but shared marker accepts only flat spec path; no component-specific approval marker exists
- flat approval is not claimed as component approval

## QA fallback

- thorough policy: 2 deep + 2 fast upper bound; no fact checker/external adversary; max round 2
- deep/fast roles available; independent runs 0
- reason: depth-2 stage cannot open forbidden depth 3
- fallback: inline multi-axis review in `plan_reviews/round_1.md`; assurance claim is inline only

## Separability

Code-plan file-only handoff is complete and source read-only. Future code-execute owns mutation; test/report paths are disjoint. No SD-17 inline source exception and no child dispatch.

## Quantitative locks

- digest `sha256(session-id)[:32]`; file <=8 KiB; directory <=256 and <=2 MiB
- zero enum: normal, unknown, native, same_band, degraded, timeout_or_error
- existing directive <=240 inserted UTF-8 bytes, exact strings preserved
- history <=3 increments; n>=30; multi-stratum n>=10
- required+safety 100%; hard regression 0
- both quality LCBs >=-0.02; both observed-delta LCBs >0
- paired bootstrap 10,000, seed 20260713
- max verdict eligible; adoption pending; production dynamic false/absent

## Tool contracts

- code-plan: instruction-only native Skill/plugin plus explicit guards
- dev/refactor: portable, normal Codex read/edit guards
- verification-runner: required downstream
- OpenCode Phase 2 automatic accounting/Phase 3 CLI projection: unsupported/deferred
- external adversary: not selected

## Completion

- plan/checklist/review/metrics written: yes
- source/spec/dev_logs/test_logs/pipeline summary changed: no
- child dispatch/commit/push/merge/cleanup: none
- verdict: `READY_FOR_CODE_EXECUTE / PASS_WITH_INLINE_QA_FALLBACK`

## Main integration hardening separability

After the registered stage graph completed, main performed one boundary-coupled
hardening pass across the Phase 2 lifecycle receipt, accounting schema/store,
Phase 3 strict evaluator schema, focused tests, frozen candidate hash, and
required Claude mirrors. These changes are non-separable because splitting the
receipt/output authority from its exact accounting tests, or the evaluator from
its frozen manifest/mirror, would create transiently invalid evidence and
overlapping worktree ownership. No further child dispatch was used; all prior
rows were harvested first, and the post-hardening diff requires a fresh complete
verification matrix before integration.

## Final verification

- independent review: BLOCKED with 3 blocking, 1 high, 1 medium; all fixed
- independent re-review: PASS, no blocking/high/medium
- focused: Phase 2 21, Phase 3 10
- Fleet: 221
- portable guards: 344/0 (collision-free isolated run)
- adaptation negative/boundary: pass/pass
- candidate hash: `11288b737241598dcf585eb762cfc033f3cbcca70eee6ff583cb6065f6de3606`
- production dynamic: absent; adoption: pending; real paired evidence: 0
