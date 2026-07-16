# Execution Metrics

- intensity: standard
- spec-significance: SPEC-SIGNIFICANT
- starting revision: `8ceb3cbd`
- worktree: `/home/Uihyeop/agent_setting-wt/oncall-proposal-promotion`
- stage execution: inline exception
- exception reason: the write-event window, project cursor, dispatcher mode,
  applier focus gate, and receipt assertions share one authority boundary and
  require sequential semantic-anchor changes. Native sub-agent delegation is
  unavailable under the current session policy; splitting this tightly coupled
  path would add handoff risk without independent write classes.
- independent QA claim: none unless a distinct reviewer actually runs
