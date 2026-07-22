You are the registered dispatch-depth-1 `autopilot-code` owner for the final
review/test/report continuation of the already-approved Fleet v16 strong route.
You are not alone in the repository: preserve every concurrent/user change,
do not revert unrelated edits, and do not commit, push, merge, or clean. The
root orchestrator owns integration. Do not invoke a live title provider.

Worktree:
`/home/Uihyeop/agent_setting-wt/fleet-unified-stage-ui`

Canonical artifact root:
`/home/Uihyeop/agent_setting/.agent_reports`

Immutable route:
`/tmp/fleet-unified-stage-ui.ammXPV/route.json`

Route identity:
`rt-dfec3aabe921b37f`
`sha256:dfec3aabe921b37fa9da8973c530b48ea92b7a9cd8fa9cdff7a7dd950512d404`

Registry digest:
`sha256:17ac6ae656c5a9f6054195f290cd9723b1de57a28072347d1fbbbbe34602e6f9`

Parent interactive session:
`019f8831-bc87-77f3-9315-d79cba9dd147`

This continuation exists because the implementation correction is complete and
781/781 Fleet tests pass, but its depth-2 worker and first owner misclassified a
concurrent adaptation-boundary run. Do not repeat or relabel that mistake.

Read completely before acting:

- `core/CORE.md`, `core/WORKFLOW.md`, `core/CONVENTIONS.md`, `core/OPERATIONS.md`
- the Codex adapter bootstrap and complete native `autopilot-code` Skill
- `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/plan.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/checklist.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/phase_review_followup.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/orchestrator_repro.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/root_post_execute_findings.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_review_correction.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/root_sequential_boundary_recheck.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/owner_handoff_followup.md` as historical context only

The root sequential adjudication is authoritative for the false-negative gate:
the correction worker started `adaptation-guard.test.sh` and
`check-adaptation-boundary.sh` concurrently. The guard intentionally replaced
two hashes with `-` and grew CLAUDE.md by one byte while the boundary read them.
After guard restoration, root ran guard then boundary sequentially in one
`set -e` shell; both passed and before/after `git status` was identical. Do not
edit those unrelated files and do not treat the superseded historical FAIL as a
source defect.

Your scope is continuation, not another implementation correction:

1. Inspect the complete final diff and verify the correction artifact/evidence.
2. Dispatch a **fresh independent cross-harness** review on route node
   `impl-review`, with a distinct slug and the route's assigned review contract.
   Prefer the checked Claude fallback already used by this route. Its prompt
   must read every review/root finding above plus the root sequential
   adjudication, inspect the final diff, reproduce all nine correction groups,
   and write a new report path such as
   `_internal/dev_reviews/phase_review_final.md` without overwriting history.
3. Require the reviewer to cover, not merely infer:
   - main Session single-node and record-ordered parallel stage/progress at
     168/120/100/60, including generic child-contract masking and explicit
     invalid fail-closed behavior;
   - sealed `survey -> {claim-a,claim-b} -> synth` through route, breadcrumb,
     group, process, provider-disabled demo, and populated old-key-only JSON;
   - effective title default 3/hard 4 and central governor admission of four,
     with fifth rejected and no bypass of global limits;
   - the OpenCode live-WAL private snapshot seeing an uncheckpointed exact-row
     while source DB/WAL/SHM/journal bytes and write metadata stay unchanged;
   - compose-on-demand/compiler/capability-route compatibility, no fixed stage
     vocabulary, no live provider call, mirror parity, and full tests.
4. Bind `impl-review` only for a genuine PASS with no red/yellow v16 obligation.
   If it reports a substantive defect, stop and hand the exact finding to root;
   do not mutate source in this continuation.
5. On review PASS, dispatch the route's registered `test` and `report` nodes in
   order, using their assigned contracts and write scopes. Run adaptation guard
   and boundary **sequentially**, never concurrently. Produce durable follow-up
   verification and report artifacts and exact attempt-bound completion markers.
6. End with a truthful owner handoff that names the fresh review verdict, test
   counts, sequential boundary result, warnings, and remaining root-only
   integration steps.

Use registered workers, not native collaboration agents. No dispatch depth 3.
Poll synchronously until terminal and harvest every child row. Final QA remains
`plan-check:selected-independent-pass:final-verify`.

End with the owner kernel's exact three-line handoff and nothing after it.
