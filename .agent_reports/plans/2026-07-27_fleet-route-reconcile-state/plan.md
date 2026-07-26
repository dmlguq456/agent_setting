# Fleet route reconciliation state

## Route

- Primary: `autopilot-code / debug / standard / tracked`
- Secondary: `autopilot-spec / update / standard / tracked`
- Spec significance: **SPEC-SIGNIFICANT** — the public route-node state vocabulary and
  terminal UI glyph contract change.
- Inline exception: the current Codex collaboration policy forbids spawning agents in this
  turn. The sealed standard routes remain the tracking contract, while framing, review,
  implementation, and verification are realized synchronously in the acting session.

## Problem

Fleet currently maps every open route job whose liveness is `stale` or `dead` to route-node
`failed`. An exact `terminal-observed/reconcile-needed` attempt is intentionally kept open
until its owner publishes the completion marker, so this valid intermediate state is rendered
as `✕` even though no failure has been established.

## Plan

1. Amend the Fleet PRD with a distinct `reconciling` route-node state that does not imply
   completion or gate passage.
2. Classify only exact shared-observer `reconcile-needed` evidence as `reconciling`; retain
   `failed` for generic stale/dead/killed evidence.
3. Render reconciliation with a yellow ellipsis (`…`, process label `…gate`) across breadcrumb,
   DAG detail, process card, and parallel-group projection.
4. Add hermetic regressions for exact reconciliation, generic stale failure, marker promotion,
   parallel aggregation, glyphs, widths, JSON projection, and canonical/Claude mirror parity.
5. Run focused and full Fleet verification, generated-projection checks, adaptation boundary,
   integration verification, push, and guarded worktree cleanup.

## Non-goals

- Do not change the dispatch observer or completion-marker protocol.
- Do not mark a node done before a valid marker exists.
- Do not advance successors or count reconciliation as completed progress.
- Do not mutate the live BC_ResNet_tf registry to manufacture a smoke state.
