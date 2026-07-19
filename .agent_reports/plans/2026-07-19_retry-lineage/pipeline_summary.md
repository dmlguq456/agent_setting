# Pipeline summary — SD-67 mutation-node retry lineage

- Route `rt-e6ed0326b81b2778` · autopilot-code dev/refactor · standard · staged depth-2 · tracked/within-spec.
- Governing: `spec/stage-dispatch/prd.md §13.9.1 SD-67`.
- **Pipeline verdict: PASS — after round-2 depth-0 fix-forward** (round-1 FAIL history
  preserved below: implementation green; one confirmed doc-contract defect blocked the gate,
  fixed by `9196282a` and re-verified in `test_logs/verification_round2.md`).

## Stage ledger

| Stage | Harness / model | Attempt | Result | Marker |
|-------|-----------------|---------|--------|--------|
| plan | codex (deep maker) | att-11f2218c… | PASS (recovered by depth-0) | ✓ `plan.json` |
| execute #1 | codex (fast implementer) | att-bf483834… | BLOCKED — sandbox git read-only | — (harvested) |
| execute #2 | claude sonnet (fast implementer) | att-e0d7556… | PASS | ✓ `execute.json` |
| test | codex gpt-5.6-sol (deep reviewer) | att-c61046ed… | FAIL finding + BLOCKED artifact persist | — (evidence salvaged) |
| fix-forward (depth-0, round 2) | claude | — | PASS — commit `9196282a` (prose only) | — |
| test (round 2) | claude depth-0 re-verify | — | PASS (`test_logs/verification_round2.md`) | ✓ `test.json` |
| report | conductor synthesis + depth-0 round-2 addendum | — | final_report.md | ✓ `report.json` |

## Outcome

- Commits: `92f25ea0` (core-first, core-only) → `9b43d754` (guard + tests + 3 wrappers + 2 byte-identical references). Core precedes derived. Worktree clean.
- Verification: 75 Python unittest cases + 3 SD-15 shell suites + dispatch-route all pass, zero failures; all six SD-67 acceptance/exclusion assertions genuinely correct; reference byte parity holds; no out-of-scope diff.
- **Blocking defect:** `dev-pipeline.md` (both mirrors, line 115) says retry on the "unchanged
  route/attempt" while requiring "a different prior attempt" — contradicts the shipped
  `--current-attempt` exclusion and v3 duplicate-claim. Correct wording: "unchanged route with a new
  attempt identity." Prose-only; code is correct. Fix-forward list in `final_report.md §Fix-forward`.

## SD-64 replacement / orphan history (honest)

- Original conductor orphaned the cycle by ending its turn to "wait" after dispatching plan; depth-0 recovered the plan marker.
- This replacement conductor ran execute → test. execute #1 (codex) BLOCKED on read-only linked-worktree git metadata; harness re-selected to claude (recorded reason), which committed the preserved core edit and finished PASS on a new attempt id — no `git reset --hard`.
- test (codex) produced complete verification but could not persist its artifact (`.spec-grounding` read-only); conductor salvaged the evidence into `test_logs/test_report.md`.
- Two codex attempt rows remain registry-`open` (namespace-local, no terminal heartbeat → reconcile declined); harvested and terminal in fact, left as audit records.
- Lesson: codex depth-2 workers cannot reliably complete commit/artifact-producing stages in this linked-worktree + read-only-`.spec-grounding` environment.

## Artifacts (plan root `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_retry-lineage/`)

- `plan/plan.md`, `plan/checklist.md`
- `dev_logs/execute-claude.md` (execute evidence)
- `test_logs/test_report.md` (salvaged independent review + FAIL finding)
- `final_report.md` (this cycle's synthesis + fix-forward list)
- `pipeline_summary.md` (this file)
