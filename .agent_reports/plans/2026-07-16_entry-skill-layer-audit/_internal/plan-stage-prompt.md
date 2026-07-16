# Assigned code-plan stage

This is the planning stage only. Treat the entire source worktree as read-only:
do not run generators or checks that can rewrite files, and do not create,
edit, rename, or delete any worktree file. The prior r2 planning attempt was
terminated after it crossed that boundary; do not reuse or continue its source
actions. Write only the canonical cycle plan artifacts named below.

Plan the approved entry-skill-layer audit/refactor in
`/home/Uihyeop/agent_setting-wt/entry-skill-layer-audit` at thorough intensity.

Required inputs:

- Task spec: `/home/Uihyeop/agent_setting/.agent_reports/spec/skill-design-refactor/prd.md`
- Prior worker-bootstrap result: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_worker-bootstrap-v5/final_report.md`
- Owner route: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit/_internal/route.json`
- Cycle root: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-16_entry-skill-layer-audit`

Scope the plan to audit and refactor all 13 primary entry-router Skills, keeping
worker-bootstrap v5 intact. Preserve the required order: portable core and
capabilities; canonical Skills, references, and generators; then Claude,
Codex, and OpenCode projections. Separate pre-approval routing metadata from
post-approval owner execution contracts. Plan deterministic static-size,
routing, projection, and Skill-conformance verification, generated-output
refreshes, baseline comparison for unrelated failures, commit, and task-branch
push. Explicitly protect concurrent fleet-usage commits and avoid primary
checkout source edits.

Write durable `plan.md`, `checklist.md`, and `_internal/plan_reviews/plan-check.md`
under the cycle root according to the assigned stage contract. Record
`spec-significance: within-spec`. Do not implement source changes.
