# Plan: core-first guard and recall-first

## Scope

- Make the loop-engineering first principle explicit in core before adapter edits.
- Extend the canonical memory recall contract with recall-first behavior and a read-only `memory-scout` capability shape.
- Add deterministic core-read marker and core-first adapter edit guard.
- Derive the behavior into Claude, Codex, and OpenCode adapter surfaces.

## Spec Significance

spec-significance: SPEC-SIGNIFICANT — this changes the memory recall contract and adapter guard behavior for the harness itself. `spec/prd.md` was read and will receive a minimal delta note.

## Order

1. Update core source of truth: `DESIGN_PRINCIPLES.md`, `MEMORY.md`, hook/adaptation docs, drill entry.
2. Implement portable guard scripts under `hooks/`.
3. Map the guard and recall behavior into Claude, Codex, and OpenCode.
4. Verify deterministic guard behavior, adapter readiness checks, selected drill, and requested Claude audit.
