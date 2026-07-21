# Code-execute stage assignment

Implement the approved plan in
`/home/Uihyeop/agent_setting-wt/depth1-surface-terminology-remediated`. This is
route node `execute`, assigned contract `code-execute`. Work only in the source
worktree plus the canonical artifact paths allowed by the route.

Required inputs:

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/plan.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/checklist.md`
- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/_internal/metrics.md`
- governing spec `/home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch/prd.md` v20 §13.12 / SD-73–75
- audit `/home/Uihyeop/agent_setting/.agent_reports/documents/2026-07-20_depth1-surface-terminology-audit.md`

Start by confirming the worktree is clean at `d7e5ad35` / current
`origin/main`. Enumerate the files in approved commits `7094c92b` and
`c95ed391`, run the required preflight write guard before each prospective
source edit, then apply only those commits with
`git cherry-pick --no-commit 7094c92b c95ed391`. Resolve their intent against
current main and amend/extend it to satisfy the entire plan and PRD v20. Do not
cherry-pick, reproduce, or introduce the rejected `6b3a34bc`
co-primary/multi-capability composition contract. Leave the original branch
unchanged.

Implement all required qualified schema names, closed namespaces, strict
quick registered-headless-only behavior and zero-emission failures, direct and
standard+ preservation, four distinct runtime surfaces, legacy migration
rules, completion/registry/Fleet consumers, deterministic tests, and generated
sibling projections. Use repository generators/sync tools for generator-owned
files. Keep `agents.max_depth` unchanged as the Codex-native setting.

Write detailed step logs under
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_depth1-surface-terminology-remediation/dev_logs/`
and update `checklist.md` with actual completion/evidence. Run focused
implementation checks needed to avoid handing syntactically broken work to the
test stage, but leave the independent full verification and risk review to
`code-test`. Do not commit: the owner may commit only after a test-stage PASS.
End with the worker kernel's exact three-line handoff.
