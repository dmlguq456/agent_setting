# Code-execute evidence

## Result

The registered `code-execute` worker produced the source diff but returned
`BLOCKED` because its workspace-write sandbox could not create the canonical
spec-read marker under the primary checkout. The depth-1 owner recovered the
source diff from the shared worktree and materialized this canonical log under
the assigned execute write scope.

## Changed surfaces

- Portable contract: `core/WORKFLOW.md`, `core/CONVENTIONS.md`, and the ten
  autopilot entry capability contracts that did not already expose an entry
  load-phase row.
- Canonical/Claude layer: 13 compact entry routers plus one-level
  `references/owner-execution.md` bodies and Claude marketplace copies.
- Generation: `tools/sync-entry-skill-layer.py`, manifest helpers, Claude
  metadata ordering, and the aggregate generator.
- Checks: `tools/entry-skill-layer.test.py`, Skill conformance, routing
  contract expectations, and manifest generation.

## Focused evidence reported by the worker

- `python3 tools/entry-skill-layer.test.py`: PASS; 13 entries; canonical and
  Claude totals 26,825 UTF-8 bytes each.
- `bash tools/skill-conformance/check.sh`: PASS.
- `sh tools/routing-contract.test.sh`: PASS after replacing stale compact
  router expectations.
- `sh tools/generated-projections.test.sh`: completed in the focused stage run.
- `python3 tools/generate.py --check`: completed in the focused stage run.
- `git diff --check`: PASS.

These are implementation-stage checks only. The assigned `code-test` stage
must re-run and independently inspect semantic preservation, moved-reference
links, generated parity, worker-bootstrap v5 hashes/bytes, and unrelated
baseline failures before the owner accepts the change.
