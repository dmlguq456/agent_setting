# code-plan assignment — Codex native subagents in Fleet

Produce the durable implementation plan and checklist for the approved Fleet
feature. Read only the assigned `code-plan` stage contract and these inputs:

- `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-20_codex-fleet-native-subagents/_internal/owner-assignment.md`
- `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` (F-29 and v11 amendments)
- relevant `tools/fleet/` source/tests and canonical Claude mirror
- current official Codex subagent manual and Claude parity reference named in the owner assignment
- read-only `$CODEX_HOME/state_*.sqlite` and `$CODEX_HOME/sessions/**/rollout-*.jsonl`

Ground the design in observed Codex runtime records. Separate runtime support,
passive Fleet projection, and remaining gaps. Attribution must fail closed;
subagents are enrichment only; Fleet must never mutate Codex runtime state.

Write `plan.md`, `checklist.md`, and a risk-focused plan review under
`_internal/plan_reviews/`. Include exact intended files, fixture matrix,
live-smoke method, mirror-parity handling, and the full required verification
set from the owner assignment. Record the spec-significance verdict. Do not
edit source code, commit, push, or clean the worktree.
