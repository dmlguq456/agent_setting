# Fleet memory sync-event attribution — pipeline summary

## Outcome

The code cycle passes its assigned in-scope gates. Fleet previously showed only `agent_setting` because `migrate`/`sync` absorbed records into the DB without emitting write-journal events. Using a process-cwd fallback for those events would have attributed every cross-project absorption to the repository running sync, also misreporting the source as `agent_setting`. The implementation now emits prospective, create-only `action=add` events with literal `actor=sync` and the logical cwd of the absorption source.

Sources are attributed as follows: decoded auto-memory project cwd; resolved post-it repository root; valid legacy Markdown cwd; and no cwd for global profiles or undecodable/invalid sources. The Fleet collector remains unchanged because the real producer event is consumed and grouped correctly.

## Changed files and behavior

- `tools/memory/mem.py`: added explicit event-cwd handling, insert-only journal controls, literal sync actor forwarding, and source-specific migrate wiring. Existing manual add/note telemetry retains its ambient cwd and all mutation branches.
- `tools/memory/mem_cluster_j.test.sh`: added hermetic producer/consumer, hostile-environment, idempotency, no-backfill, cwd omission, filtered-log, sync-isolation, and runtime-fencing coverage.
- `tools/fleet/collectors/memory.py`: unchanged.

The live linked worktree diff is limited to those two approved files: 517 insertions and 18 deletions. No schema, historical journal rewrite/backfill, real runtime store, commit, push, merge, or cleanup operation was performed.

## Verification evidence

Required assurance: `preflight.sh qa-policy standard code` → `plan-check:selected-independent-pass:final-verify`. The final implementation review is PASS at [`_internal/dev_reviews/phase_review_r2.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/dev_reviews/phase_review_r2.md), and independent verification is recorded at [`test_logs/verification.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/test_logs/verification.md).

- Focused Cluster J: 44/44 PASS.
- Focused Fleet F-19: 26/26 PASS.
- Full Fleet discovery: 744/744 PASS.
- Other canonical memory suites: inject 21/21, Cluster E 31/31, Cluster E gamma 40/40, repairs 38/38, retrieval 22/22, pending drain 23/23, retrieval eval 9/9, plus empty-store guard PASS.
- Syntax/AST, CLI help, adapter launchers/symlink, manifest, adaptation-boundary, approved-path, collector-unchanged, and `git diff --check` checks passed.
- Repeat migrate preserved DB row/source/strength snapshots and journal line count; pre-seeded rows and journal sentinels remained unchanged, providing the prospective-only/no-backfill guarantee.
- Fenced sync used a fresh empty non-Git store, explicit `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`, isolated memory paths, and matching before/after snapshots of real runtime state and worktree state.

## Remaining risk and handoff

`bash tools/memory/distill.test.sh` remains a visible owner-accepted baseline warning: raw result `PASS=35 FAIL=2`. The failure files are zero-diff against the sealed baseline and outside the approved implementation scope; the exact narrative has an ambient-dispatch variance documented in [`phase_review_r2.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/dev_reviews/phase_review_r2.md). The adaptation-boundary check also retains its pre-existing documented warning about 126 concrete Claude/model references.

The spec owner report is PASS at [`_internal/spec-owner-report.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-owner-report.md). The branch `fleet-memory-sync-events` remains an uncommitted linked-worktree handoff at sealed HEAD `e8938809d87e54474f5e7242a2552598c2636a0a`; integration, commit, push, and cleanup remain the depth-1 owner's responsibility.
