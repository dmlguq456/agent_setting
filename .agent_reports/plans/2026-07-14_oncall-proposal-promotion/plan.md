# On-call Proposal Promotion — Implementation Plan

## Goal

Connect the existing nightly on-call agent to the offline improvement inbox so
recent memory-backed incidents can become deduplicated proposals without
granting the loop any source, plugin, runtime-config, review, adoption, or
activation authority.

## Spec significance

SPEC-SIGNIFICANT. Governance PRD v1 explicitly excluded cron/on-call wiring;
v2 now permits one scheduled collector with a `proposed` ceiling.

## Implementation

1. Extend `observe` with an agent-authored exact `incident_key`.
2. Under the existing inbox lock, append recurrence evidence and incoming
   context to the one matching record instead of creating a duplicate.
3. Fail closed if the same key appears in multiple records; never modify the
   existing proposal state during recurrence ingestion.
4. Preserve the old base during recurrence; allow only an explicit,
   current-context-bound reproduction to rebase a pre-review proposal.
5. Update the on-call contract to inspect recent memory events, read selected
   full bodies, corroborate against current evidence, and promote at most to
   `proposed`.
6. Synchronize the collapsed Claude loop projection; leave Codex/OpenCode loop
   execution ownership unchanged.
7. Add functional and contract tests, then run generation, adapter-boundary,
   runtime activation, extension, and release regressions.

## Verification

- proposal unit/functional tests, including exact-key concurrency and terminal-state recurrence;
- on-call prompt contract assertions;
- Python compile and shell syntax;
- generator and generated-projection checks;
- adaptation boundary and skill conformance;
- runtime activation, extension lifecycle, and managed release lifecycle.

## Safety

- Memory remains a discovery hint; proposal evidence requires a current live source.
- Exact matching is mechanical; semantic identity remains agent-owned.
- Recurrence ingestion appends evidence only and cannot reopen or change state.
- No new apply, activation, runtime CLI, network, hook, or runtime-config command.
