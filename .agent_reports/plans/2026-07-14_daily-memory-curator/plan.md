# Daily Memory Curator — Implementation Plan

## Goal

Keep the session-end curator primary while adding one daily on-call catch-up over
memory changed since each project's last successful cursor. Reuse the guarded
no-tools curator path and report every action without granting source, plugin,
runtime-config, proposal, or activation authority.

## Spec significance

SPEC-SIGNIFICANT. Root memory PRD v19 adds D-42; the improvement-governance
component v3 explicitly separates the memory-maintenance sidecar from proposal
promotion.

## Implementation

1. Add read-only `project-key` and event-windowed `curate-recent` CLI surfaces.
2. Add a strict daily mode to the shared dispatcher and applier: recent-ID
   prune/graduate, merge-with-recent, validation before application, and no
   add/reinforce/delete/consume/reattribute.
3. Add a project orchestrator with stable per-project cursors, bounded discovery,
   atomic XDG state, fail-closed overflow/journal-gap detection, and bounded receipts.
4. Run it before the Claude on-call agent; the report phase reads its receipt.
5. Keep session-end behavior byte-compatible and leave runtime-owned config,
   installed plugins, and active projections untouched.

## Verification

- Isolated memory DB/journal tests for cursor windows and focus enforcement.
- Stub no-tools worker tests for success, no-op, failure, merge scope, pending
  protection, receipt completeness, and cursor retry.
- Existing distill, memory telemetry, on-call prompt, generation, adapter
  boundary, and projection regressions.

## Safety

- Cursor advances only after worker, strict apply, and mirror sync success.
- Mixed valid/invalid output performs no mutation; journal rotation cannot
  silently advance a cursor across discarded events.
- Pending/global/profile/other-project records remain mechanically unreachable.
- Graveyard remains fail-closed for prune/merge and dump mirror remains the
  recovery source.
- No self-edit, source edit by a loop, runtime config edit, plugin installation,
  proposal adoption, drill, or live on-call run is part of verification.
