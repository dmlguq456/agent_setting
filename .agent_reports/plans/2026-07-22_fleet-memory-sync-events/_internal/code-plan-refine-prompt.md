This is the bounded retry of route node `plan` (`code-plan`) for `rt-d7392fcfbc9ce241`. Do not edit source, specs, tests, or dispatch another worker.

Revise the existing `plan.md` and `checklist.md` in place. Preserve all sound content from the original plan and address the durable plan-check findings in `_internal/plan_reviews/round_1.md` plus this owner reconciliation:

- add an explicit full relevant memory-suite command set covering every canonical `tools/memory/*.test.sh` suite affected by shared `write_record()` / `_append_write_event()` plumbing, and full Fleet unittest discovery; name and justify any exclusion;
- fence every `sync()` acceptance invocation with `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`, a fresh non-Git `MEM_STORE`, and before/after isolation evidence for real runtime store/profile/journal/dump and the worktree;
- keep a separate repeat `migrate --apply` idempotency assertion and use `sync` only for lifecycle/index/export integration under the fence;
- add deterministic registered-post-it `action=add`, literal `actor=sync`, exact repo-root `cwd`, and Fleet `by_repo["agent-note"]` proof;
- add `mem log --json --actor sync` and explicit invalid cwd omission cases (absent key, not null or ambient fallback);
- add an executable approved-path diff check limited to `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh` unless evidence proves a collector change is necessary;
- use the canonical absolute spec inputs under `/home/Uihyeop/agent_setting/.agent_reports/spec/` and revalidate the required D-37 v22 / F-19/F-35f v15 text immediately before execution. The sealed route's satisfied `tracked_gate_evidence.spec_read` and completed spec-owner report are authoritative prerequisites; do not require this linked code worktree to contain or commit canonical artifact-root spec edits.

Write only:

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/plan.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-memory-sync-events/checklist.md`

Complete the exact `plan` marker/attempt and return the kernel's exact three-line handoff.
