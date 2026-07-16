# Assigned code-execute stage

Implement the approved plan in the task worktree only:
`/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit`.

Inputs:

- Plan: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/plan.md`
- Checklist: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/checklist.md`
- Plan check: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/_internal/plan_reviews/plan_check.md`
- Task spec: `/home/Uihyeop/agent_setting/.agent_reports/spec/skill-design-refactor/prd.md`
- Worker-bootstrap v5 result: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_worker-bootstrap-v5/final_report.md`
- Immutable route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/_internal/route.json`

Carry out the plan completely. Keep source edits inside the task worktree and
write stage logs/checklist updates only under the canonical cycle root. Run the
required preflight write guard before every file edit. Core/capabilities must be
edited first, followed by canonical Skills/references/generators, then the
Claude/Codex/OpenCode projections. Refresh generated outputs through the
repository generators; do not hand-edit generated files.

Protect these invariants:

- all 13 and only the 13 manifest entry routers are covered;
- concrete English `Use when` and `Not for` metadata remains authoritative;
- parent-invoked and model-support Skills remain outside primary routing;
- pre-approval metadata is separate from post-approval owner execution;
- official runtime support, local projection, and physical masking stay
  separate, with no unverified masking/token/cost-savings claim;
- `roles/worker-bootstrap.md`, `roles/worker-types/**`, dispatch/prompt-builder
  behavior, and worker-bootstrap v5 measurements remain unchanged;
- preserve concurrent fleet-usage changes and do not edit primary-checkout
  source.

Implement static size, routing, projection, link/anchor, and Skill-conformance
checks. Run focused checks needed during implementation, update the checklist,
and write detailed dev logs. Leave final thorough verification, commit, and
push to the owner/test/report stages.
