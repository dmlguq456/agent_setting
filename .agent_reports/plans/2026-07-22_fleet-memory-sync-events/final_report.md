# Fleet memory sync-event attribution — final report

## Outcome

PASS for the assigned code-report gate. Fleet previously showed only `agent_setting` because DB absorption by `migrate`/`sync` was quiet: it created/absorbed records without journal events. A process-cwd fallback would have made cross-project absorption appear to belong to the repository that happened to run sync, which is why it would also misattribute those records to `agent_setting`.

The delivered behavior is prospective and create-only. Newly absorbed records emit the existing journal vocabulary `action=add`, with literal `actor=sync`, and use the logical cwd of the source project. Repeat absorption, source upsert, body-dedup reinforcement, and historical rows do not create absorption events. The existing Fleet consumer remains unchanged and consumes the producer events correctly.

## Implementation

Changed worktree files:

- `tools/memory/mem.py` — added a sentinel-backed event-cwd override, source-cwd decoding, insert-only journal controls, literal actor forwarding, and wiring for auto-memory, post-it, global profile, and legacy Markdown migration sources.
- `tools/memory/mem_cluster_j.test.sh` — added isolated coverage for manual telemetry compatibility, hostile ambient attribution, post-it-to-Fleet grouping, repeat migration, fenced sync, duplicate normalization, no-backfill preservation, valid/invalid cwd cases, and `mem log --json --actor sync` filtering.

The live diff is 59 additions/17 deletions in `mem.py` and 458 additions/1 deletion in the focused test, for 517 additions and 18 deletions total. `tools/fleet/collectors/memory.py` is byte-unchanged. No schema migration, journal replay, historical backfill, real runtime-store mutation, commit, push, merge, or cleanup was performed.

## Evidence

The standard QA assurance is `plan-check:selected-independent-pass:final-verify` from `preflight.sh qa-policy standard code`. The final code review is PASS in [`phase_review_r2.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/dev_reviews/phase_review_r2.md); independent verification is in [`verification.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/test_logs/verification.md).

- Cluster J: 44/44 PASS.
- Fleet F-19: 26/26 PASS.
- Full Fleet discovery: 744/744 PASS.
- Additional memory suites: inject 21/21, Cluster E 31/31, Cluster E gamma 40/40, repairs 38/38, retrieval 22/22, pending drain 23/23, retrieval eval 9/9, and empty-store guard PASS.
- Syntax/AST, CLI entry/help, Codex/OpenCode launcher help, Claude symlink, manifest, adaptation-boundary, approved-path, collector-unchanged, and whitespace checks passed.

The no-backfill guarantee is evidenced by unchanged pre-seeded row/source data and journal sentinel, unchanged DB/source/strength and journal-line snapshots on repeat migrate, and zero event emission for existing sources, dedup reinforcement, and repeat absorption. The fenced sync proof used a new empty non-Git store, isolated paths, explicit `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`, and equal before/after snapshots for real memory/profile/journal/dump and worktree state.

## Remaining risk

`bash tools/memory/distill.test.sh` remains a visible warning at `PASS=35 FAIL=2`. The owner disposition accepts it as a deterministic, pre-existing, zero-diff baseline exception outside the two approved files; it is not waived as an in-scope regression. The final review additionally records that the precise sub-failure signature varies with ambient dispatched-worker environment, while the zero-diff baseline conclusion remains unchanged. The adaptation-boundary check retains its pre-existing warning about 126 concrete Claude/model references.

## Handoff

The spec-owner report is PASS in [`_internal/spec-owner-report.md`](/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/_internal/spec-owner-report.md). The linked worktree branch `fleet-memory-sync-events` is intentionally uncommitted at sealed HEAD `e8938809d87e54474f5e7242a2552598c2636a0a`, with only `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh` modified. The depth-1 owner receives the diff and evidence for authorized integration, commit, push, and eventual cleanup.
