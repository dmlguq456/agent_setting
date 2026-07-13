# Spec Metrics — token-self-regulation

## Inputs

- research: done, 25 sources, 22 cards, thorough QA
- official docs: Codex developer commands + config reference, checked 2026-07-13
- local runtime: codex-cli 0.144.1
- local features: rollout_budget=false, token_budget=false, runtime_metrics=false (all under-development)
- local native config probe: documented shape rejected; undocumented requested field also rejected by schema

## Routing

- capability: `autopilot-spec` (`instruction-only`)
- worktree: `/home/Uihyeop/agent_setting-wt/token-self-regulation`
- branch: `token-self-regulation`
- intensity for implementation: `thorough`
- spec significance: `SPEC-SIGNIFICANT`

## Independent read-only review

- surface review: shared telemetry + explicit Fleet fields + transition-only Codex hook
- risk review: intensity/safety/dispatch invariants and native probe gate
- conflict resolved: research suggestion “tight → dispatch suppression” removed

## Headless fallback

`adapters/codex/bin/preflight.sh headless --check` failed before registry writes because runtime projection check reported `hooks-json:failed reason=not-harness-hook-projection`. Hook trust itself was present. Per Codex adapter fallback, spec work continues manually inside the dedicated worktree; no headless completeness claim is made.

## Reinjection budget

- normal/unknown/native/same-band: 0 bytes
- tight/critical band entry: <= 240 UTF-8 bytes, one line
- savings claim: prohibited until Phase 2 measurement

## Intake gate

Skipped: the user had already completed the research direction, explicitly listed the remaining phases, and explicitly resumed implementation. No unresolved irreversible design choice remained for Phase 0–1.
