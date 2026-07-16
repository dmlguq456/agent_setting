# Plan Check Evidence

Date: 2026-07-16
Plan: `plans/2026-07-16_entry-skill-layer-audit/plan.md`
QA policy: `thorough code`
spec-significance: within-spec

## Assurance status

`preflight.sh qa-policy thorough code` reported:

- quality reviewers: `2x-deep-reviewers+2x-fast-reviewers`
- assurance scope: `plan-check:selected-independent-pass:final-verify`
- independence may be claimed only when a separate Codex/headless/external pass
  actually runs
- fallback: report inline review when an independent agent is unavailable

This bounded stage is forbidden to dispatch another worker, so four explicit
inline review lenses were run by the same worker. They are not independent
reviews. Final implementation verification remains mandatory.

## Deep lens 1 — architecture and source order

Verdict: PASS after revision.

Checks:

- The plan starts with portable core, then updates all 13 capability contracts,
  then canonical/root and Claude owner references/generation, then Codex and
  OpenCode sibling projections.
- It does not treat Claude/root compatibility Skills as portable truth or as a
  Codex/OpenCode input.
- It separates the Layer 0 route proposal from Layer 1 owner execution and
  preserves the standard+ owner/stage read boundary.
- It does not reselect capability, intensity, topology, or worker contracts.

Revision made: the owner contract is now explicitly runtime-bounded: portable
semantics stay in `capabilities/`, Claude detail moves to a Claude/root mirrored
reference, and Codex/OpenCode continue from their own native surfaces.

## Deep lens 2 — semantic preservation and migration risk

Verdict: PASS after revision.

Checks:

- All 13 names are enumerated; the plan does not accidentally include the 13
  parent-invoked/model-support Skills.
- Existing procedures are moved, not summarized away.
- A starting-commit comparator distinguishes semantic edits from required link
  path rewrites.
- The missing `autopilot-apply/references/` directory is handled.
- Relative-link depth and the known `draft-strategy` backlink are addressed.
- Capability-specific invariants (lab topology, refine routing, orientation,
  spec locking, note triage, code significance) have explicit preservation
  checks.

Revision made: added a repository-wide Markdown link/anchor scan and required
`<agent-home>` cross-root links where byte-identical root/Claude relative paths
cannot both resolve.

## Fast lens 1 — deterministic verification and baseline handling

Verdict: PASS.

Checks:

- The entry set is manifest-derived and asserted as 13.
- Every entry has a 4,096 UTF-8 byte ceiling plus exact total/max regression
  baselines; no token/cost extrapolation is permitted.
- Generation check, conformance, projection determinism, routing, adaptation,
  footprint, link integrity, and diff whitespace are covered.
- Current failures are classified before implementation: two obsolete routing
  assertions are in-scope test maintenance; legacy artifact-root and exact
  Claude-bootstrap wording are unrelated baselines.
- Mutation-based tests require immediate cleanup verification or a disposable
  copy because the planning probe demonstrated residue risk.

No open finding.

## Fast lens 2 — git, concurrency, and handoff

Verdict: PASS.

Checks:

- Source edits stay in the task worktree; durable plan evidence stays under the
  canonical artifact root.
- The plan uses focused staging, a task-branch commit, non-force push, and a
  post-fetch integration/verification cycle.
- Concurrent fleet-usage/main commits are merged intact rather than overwritten
  or silently staged.
- Worker-bootstrap/dispatch/fleet paths are explicit deny zones.
- The primary checkout is never a source-edit target.

No open finding.

## Final plan-check verdict

PASS. The plan is implementation-ready, all assigned requirements are mapped to
concrete files/checks, and no blocking ambiguity remains. Independent review was
not performed and is not claimed; the downstream test stage must provide the
selected final verification evidence required by the thorough QA policy.
