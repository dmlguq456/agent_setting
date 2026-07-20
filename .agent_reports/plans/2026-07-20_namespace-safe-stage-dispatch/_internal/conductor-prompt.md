Complete the approved `autopilot-code · strong` cycle described in:

`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_namespace-safe-stage-dispatch/_internal/task_brief.md`

Immutable route:

`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_namespace-safe-stage-dispatch/_internal/route.json`

Governing blueprint:

`/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md`

Requirements:

1. Read the `autopilot-code` owner contract and the task brief.
2. Treat the primary checkout's uncommitted wrapper diff as read-only candidate
   input. Never mutate `/home/Uihyeop/agent_setting`; all source edits belong in
   the assigned task worktree.
3. Materialize durable plan, checklist, metrics, implementation log, tests, and
   final report in the canonical cycle directory.
4. Because this is dispatch-infrastructure self-modification, record
   `STAGE_DISPATCH_INLINE_OK=dispatch-infra-self-modification`. The existing
   exit-77 guard may be used once to prove the current nested stage path
   unavailable. Do not repeatedly launch doomed sessions. Continue bounded
   plan/execute/test/report work inline in this depth-1 owner when the checked
   fallback reaches inline, and disclose that independent stages did not run.
5. Update portable core first. Adapter changes follow core. Prepare the
   stage-dispatch PRD update as an explicit transaction patch and evidence; do
   not hand-edit the canonical spec outside the owning spec transaction.
6. Implement and verify automatic namespace-safe lifecycle selection in
   `dispatch-chain` for both Codex and Claude children. Preserve detached
   behavior outside transient namespaces and do not substitute native
   subagents.
7. Do not commit, push, merge, clean worktrees, or edit runtime-owned config.
   Codex linked-worktree mutation is no-commit; depth-0 will integrate after
   PASS.

Return the exact three-line worker handoff required by the owner kernel.
