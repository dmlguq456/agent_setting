# Proposal-Gated Improvement Foundation — Final Report

## Outcome

The harness now has a concrete, inactive boundary between loop learning and
plugin/runtime activation. Loops can record incidents and evidence, but the
tool cannot edit or activate source, projections, plugins, or settings.

## Main surfaces

- `tools/improvement/proposals.py`: offline lifecycle CLI.
- `tools/improvement/proposals.test.sh`: temporary-HOME test plus real-runtime immutability guard.
- `loops/improvement.md`: operational authority and reconciliation contract.
- `core/ADAPTATION.md` and `core/DESIGN_PRINCIPLES.md`: ownership and trust-root invariants.
- `.agent_reports/spec/self-improvement-governance/prd.md`: component blueprint.

## Safety properties

- XDG state is outside repo, managed releases, and runtime homes.
- Proposal adoption and runtime realization are independent states.
- Stale proposal context blocks review/adoption.
- Runtime/plugin context change requires realization revalidation.
- Human approval references are required for review, terminal decisions, and activation/retirement records.
- There is no apply, plugin, setting, activation, Git mutation, network, hook, or cron command.

## Verification

- 11 proposal lifecycle tests passed.
- Real runtime config and harness-plugin snapshot remained unchanged.
- Generated projections, adaptation boundary, runtime activation, extension lifecycle, and managed release lifecycle passed.
- No independent agent QA is claimed; standard QA used the documented inline fallback because subagent dispatch was not permitted.

## Deferred by design

Automatic incident capture, runtime-watch ingestion, UI, authenticated approval,
source diff application, and activation remain future separately approved work.
