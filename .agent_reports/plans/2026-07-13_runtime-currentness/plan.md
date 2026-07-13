# runtime-currentness update plan

## Context

- Date: 2026-07-13 KST.
- Capability: `autopilot-code`, mode `dev/refactor`, intensity `standard`, QA `standard`.
- Stage graph: `code-plan -> code-execute -> code-test -> code-report`.
- spec-significance: SPEC-SIGNIFICANT. The task changes fleet rate-window semantics, dispatch usage policy, loop contracts, and adapter projection docs.
- Official runtime evidence used for normative claims:
  - OpenAI Codex pricing/help now describes plan-relative usage, ChatGPT credits, and token/credit-based Codex usage.
  - Anthropic Claude support continues to document Claude/Claude Code shared usage limits and reset behavior.

## Plan

1. Update the agent-fleet-dashboard PRD through update semantics: preserve the previous PRD under `_internal/versions/v3/prd.md`, then add v4/F-20 dynamic rate-window requirements with the 2026-07-13 incident.
2. Generalize fleet Codex rate-limit parsing:
   - parse `limit_window_seconds`;
   - map known durations to labels (`5h`, `7d`, etc.);
   - preserve legacy `primary=5h`/`secondary=7d` behavior when duration is absent;
   - render unknown durations honestly as a duration-derived/unknown window label rather than pretending they are 5h.
3. Update dispatch usage policy:
   - remove default `HARNESS_CAPACITY_BIAS=claude`;
   - emit neutral `auto/balanced` bias unless explicitly overridden;
   - honor known future reset values even when the marker is older than the old 300-minute window;
   - keep unknown-reset bounded.
4. Add a portable `runtime-watch` loop:
   - official Codex/Claude source checks only for normative runtime facts;
   - local runtime/projection probes;
   - report/proposal output only, no auto policy edits;
   - conservative/change-triggered scheduling to avoid token waste;
   - catalog, oncall, adapter loop-info, Claude projection, README/manifest sync.
5. Update docs/examples and focused tests.
6. Verify focused fleet tests, `utilities/usage-check.test.sh`, loop syntax/probe, projection/sync checks, `git diff --check`, doctor/boundary checks.

## Plan-Check

- Requirements coverage: all eight requested outcomes are represented above.
- Over-scoping check: no runtime policy auto-edits are delegated to the new loop; it writes reports/proposals only.
- Executable verification: target commands are unittest, shell tests, syntax checks, manifest/projection checks, diff check.
- Missed spec risk: PRD update is explicit and versioned; root memory PRD remains read-only except for context.
