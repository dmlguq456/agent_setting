# Entry Route Confirmation — Implementation Plan

Date: 2026-07-16
Capability: `autopilot-code`
Intensity: standard
Spec: `.agent_reports/spec/skill-design-refactor/prd.md` v4

## Goal

Make primary entry routing an explicit, low-cognitive-load handshake: the main
agent proposes one route from compact metadata, the user approves or corrects
it, and the selected capability owns execution without repeated confirmation.

## Steps

1. Add the confirmation and context-ownership contract to portable core policy.
2. Move invocation class, positive trigger, and exclusion boundary into
   `harness-manifest.json`; generate the conformance registry from it.
3. Generate concrete discovery descriptions and compact entry Skill bodies for
   Codex, Claude, and OpenCode without circular `Use when needed` wording.
4. Strengthen conformance and projection tests, then refresh the explicitly
   governed context-footprint baseline if measured growth remains in budget.
5. Regenerate projections and run schema, conformance, parity, footprint, and
   runtime-projection verification.

## Main-context invariants

- Depth 0 reads compact entry metadata and presents the fixed confirmation card.
- At `standard+`, depth 1 reads the full capability contract and owns routing.
- Depth 2 reads only its assigned stage contract and implementation context.
- Read-only orientation is exempt; material work does not begin before approval.
- A user message that already names and approves the route counts as approval.
- Confirmation repeats only when the proposed route or material scope changes.

## Execution topology

This run is intentionally inline. The active runtime instruction forbids native
subagent delegation unless the user explicitly requests it, so the standard
pipeline's delegation lane is recorded as an inline exception. The same QA and
artifact gates still apply.

## Verification

- Manifest/schema validation and generated-projection drift checks
- Skill invocation-policy conformance for all three adapters
- Context-footprint strict check and explicit baseline review
- Runtime projection and adapter parity checks
- Targeted shell tests plus `git diff --check`
