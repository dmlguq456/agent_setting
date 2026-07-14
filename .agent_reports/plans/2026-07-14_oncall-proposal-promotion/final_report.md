# On-call Proposal Promotion — Final Report

## Outcome

The existing on-call agent can now turn a small number of corroborated,
memory-discovered harness incidents into offline proposals. It cannot apply the
proposal or modify active source, projections, plugins, runtime settings, or
memory.

## Flow

`memory mutation lead → full-body read → live corroboration → exact-key observe
→ optional context-bound reproduction → optional proposed → human review`

Exact recurrence adds evidence to one record. It does not change state or the
base fingerprint. A stale pre-review proposal becomes fresh only after a new
reproduction bound to current runtime/source context.

## Verification

- 19 proposal/contract tests passed, including concurrent exact-key ingestion,
  terminal-state recurrence, and stale-context rebase.
- Generation, projection, adaptation, skill conformance, runtime activation,
  extension lifecycle, and managed release regressions passed.
- Runtime-owned config and harness plugin state remained unchanged.
- No drill, real on-call run, plugin update, activation, or self-edit was run.

## Operational handoff

Future morning reports may contain an `Improvement proposals` section. The
user's action is to decide whether a listed `proposed` item enters a separate
spec/code cycle. Official runtime/plugin changes still require a fresh
realization check before activation.

## Source

- Branch: `oncall-proposal-promotion`
- Worktree: `/home/Uihyeop/agent_setting-wt/oncall-proposal-promotion`
