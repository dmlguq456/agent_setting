# Plan review — dispatch-routing-policy-v7

Mode: inline `qa/plan-review` fallback. No independent QA claim: this depth-2 worker cannot dispatch depth-3.

## Requirements
PASS. SD-21~24 each maps to files, behavior, and regressions; current docs/runtime checks, core-first ordering, projection sync, Fleet hotfixes, and verification are covered.

## Scope
PASS. Core owns family/role/priorities; adapters own exact IDs/probes; selector never dispatches; Fleet changes deterministic attribution only. OpenCode remains unknown.

## Executable verification
PASS. Concrete timed commands are present. Hermetic cases cover all priority and SD-24 branches; quota-sensitive probes have fallback.

## Risks
- No major issue. Avoid API-alias-as-runtime-proof and duplicated mappings.
- Add the cross-runtime child marker before procscan logic.
- Preserve fuzzy matching only for explicitly identified legacy code rows.
- Keep the Codex runtime bootstrap discovery failure visible.

## Verdict
✅ No issues. Ready for code-execute handoff with probe/projection caveats.
