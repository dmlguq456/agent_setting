# Implementation Log

## Proposal inbox

- Added optional semantic `incident_key` identity to `observe`.
- Required named automated collectors such as `loop:oncall` to provide the key.
- Serialized exact-key lookup under the existing mutation lock.
- Exact recurrence appends bounded evidence, occurrence count, current fingerprint,
  and a same-state history event; duplicate keys fail closed.
- Capped evidence and history at 128 entries per proposal.

## Freshness reconciliation

- Recurrence ingest preserves the proposal state and original base fingerprint.
- A named collector must bind `reproduced` to a current context.
- Only that explicit pre-review reproduction rebases the stored base; a later
  human review must match the newly reproduced fingerprint.
- Reviewed and terminal proposals receive evidence only and are never reopened.

## On-call contract

- Recent memory mutations are discovery leads only.
- The agent reads selected records in full and requires live source, test, log,
  artifact, or local runtime corroboration.
- Promotion is bounded to one or two candidates and stops at `proposed`.
- No source edit, generated projection edit, plugin/runtime mutation, Git action,
  network probe, headless session, drill, human actor, or approval reference is
  authorized.

## Projection

The canonical loop files and concrete Claude loop projection are byte-identical.
Codex and OpenCode keep their existing canonical loop-guide realization; no
runtime-owned config or installed plugin was changed.
