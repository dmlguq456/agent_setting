# Pocock parity and context efficiency

- Date: 2026-07-15
- Branch: `pocock-parity-efficiency`
- Mode: `dev/refactor`
- Intensity: `standard`
- Spec: `spec/skill-design-refactor/prd.md` v3

## Goal

Restore the intended hierarchy `core/capabilities/roles -> {Claude, Codex, OpenCode}` and close Pocock adoption on all three active adapter surfaces. Reduce always-loaded context and repeated injection without lowering intensity, model role, dispatch depth, validation, tests, safety, or required input.

## Implementation

1. Add the sibling-adapter completion and context-budget contract to portable core documents; remove wording that lets one adapter stand in for another.
2. Convert all three runtime bootstraps to compact routers. Keep runtime commands and invariants there; move detailed lifecycle/edge-case explanation behind adapter README/ADAPTATION and command help.
3. Extend `skill-conformance` defaults to Claude, Codex, and OpenCode active Skill trees while interpreting runtime-specific invocation metadata through explicit adapter rules.
4. Make `context-footprint --strict` enforce bootstrap, active metadata, duplicate exposure, hook emission, and checked baseline regression budgets.
5. Regenerate capability projections from portable sources, update deterministic boundary checks, and verify the three adapters independently.

## Plan check

- Source hierarchy: no adapter becomes another adapter's generation input.
- Fairness: a shared behavior is complete only after all three adapter rows are verified or explicitly marked fallback/unsupported; otherwise overall status remains PARTIAL.
- Savings: static bytes/chars are reported as footprint, never converted to token or billing savings. Production savings claims require paired real sessions `n>=30` with input/cache/output/cost separated.
- Quality floor: output pressure may remove optional prose only; it cannot reduce rigor, tools, tests, safety, accessibility, or needed input context.
- Runtime detail loss: bootstrap reductions retain the executable command surface and point to adapter-owned detailed docs; boundary tests verify the moved detail.
