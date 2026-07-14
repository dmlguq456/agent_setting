# Execution Metrics

- intensity: standard
- spec-significance: SPEC-SIGNIFICANT
- starting revision: `65518bc3`
- worktree: `/home/Uihyeop/agent_setting-wt/oncall-proposal-promotion`
- stage execution: inline exception
- exception reason: the CLI record schema, on-call instructions, projection,
  and assertions share the same incident-key and authority boundary; splitting
  writes would create sequential semantic-anchor conflicts. Native sub-agent
  delegation is additionally unavailable under the current session policy.
  The implementation and verification commands are bounded, so registered
  headless dispatch overhead exceeds the remaining separable stage work.
- independent QA claim: none unless a separate reviewer actually runs
