# token-self-regulation implementation plan

## Context

- Date: 2026-07-13 KST.
- Capability: `autopilot-code`, mode `dev/refactor`, intensity `thorough`.
- Stage graph: `code-plan -> code-execute -> code-test -> code-report`.
- Spec: `.agent_reports/spec/token-self-regulation/prd.md` (Phase 0–1).
- spec-significance: SPEC-SIGNIFICANT. This adds a portable telemetry contract, cross-harness Fleet fields, and a Codex prompt lifecycle policy.
- Dispatch fallback: headless preflight is blocked by the installed hooks projection mismatch; stages run manually in this dedicated worktree and the fallback is recorded in metrics.

## Plan

1. Add a shared, stdlib-only token telemetry module under `tools/fleet/`:
   - parse Codex `last_token_usage` and `total_token_usage` separately;
   - preserve raw active-context and cumulative input/cache/output/reasoning/total counters;
   - implement the Codex 12k reserve context formula and deterministic normal/tight/critical bands;
   - expose exact-session rollout discovery without transcript content leakage.
2. Make Fleet semantics explicit without changing current rendering:
   - add `active_context_tokens`, `context_window_tokens`, and cumulative session counter fields to `Session`;
   - populate supported fields in Codex, Claude, and OpenCode collectors;
   - keep legacy `Session.tokens` behavior for render compatibility;
   - synchronize the canonical Fleet tree to the Claude mirror.
3. Add the portable CLI `utilities/token-budget.py`:
   - accept explicit signals or exact Codex session lookup;
   - emit `kv`, `json`, or transition-only `hook` output;
   - fail open on unknown/malformed/ambiguous/stale/decreasing counters;
   - store only per-session band/counter state under XDG user state;
   - suppress fallback output when validated native opt-in is explicit.
4. Wire the portable contract core-first:
   - add intensity/budget orthogonality and safety/input invariants to `core/CONVENTIONS.md`;
   - state in `core/OPERATIONS.md` that budget pressure cannot reduce mandatory dispatch/depth/stages/guards.
5. Wire the Codex adapter:
   - expose `preflight.sh token-budget [cwd] [session-id] [kv|json|hook]`;
   - add transition-only output to `userprompt-lifecycle.py` without disturbing mode/recall/briefing/turn-nudge;
   - update Codex bootstrap/README/ADAPTATION runtime boundaries and under-development native fallback.
6. Add focused and contract tests:
   - parser/formula/threshold/missing/ambiguous/stale/session-isolation/native/transition cases;
   - Fleet collector explicit-field semantics and canonical/mirror parity;
   - Codex preflight + UserPromptSubmit zero/transition injection;
   - boundary assertions for orthogonality, guards, and adapter mapping.
7. Run graduated verification through the Codex verification runner, fix any regressions, then write dev/test/report artifacts.

## Plan-Check

- Requirements coverage: Phase 0 measurement, Phase 1 safe response, native fallback, parity gaps, and all seven TSR invariants are mapped to steps and tests.
- Safety: no runtime config or transcript write; unknown/degraded states preserve the existing pipeline; input reduction and required-work reduction are absent.
- Architecture: `context-footprint.py`, `harness-status.sh`, `usage-check.sh`, and legacy `Session.tokens` retain their current responsibilities.
- Dispatch conflict: the research suggestion to suppress dispatch under pressure is explicitly rejected; mandatory standard+ stage topology remains unchanged.
- Reinjection: only tight/critical band transitions may emit one <=240-byte line; all other states are zero-output.
- Verification: focused unit tests precede full portable guards, adaptation boundary, doctor, and runtime projection checks.
