# Fleet post-unit migration — implementation plan

## Objective and bounded scope

Synchronize Fleet with the portable unit catalog and compositional route compiler introduced by `a132b328^..fec5350a`, without changing runtime-owned state or widening Fleet into a control plane. Preserve dispatch contract v3 and legacy jobs/route compatibility.

Spec drift verdict: **SPEC-SIGNIFICANT**. Fleet PRD v13 treated `worker_role`/stage persona and schema-v1 routes as current; v14 now defines `assigned_contract`, `unit`, `worker_type`, and `model_role` as separate axes and records topology schema v3 versus immutable route schema v2.

## Route and assurance

- Primary capability: `autopilot-code`, standard+ intent.
- Registered same-harness headless route: skipped after strict preflight failed `runtime profile activation freshness=duplicate` following unit-catalog migration; no attempt was registered.
- Registered cross-harness route: skipped because the checked profile could not be activated; no silent fallback or parity claim.
- Checked fallback: one native Codex capability owner. Two bounded native read-only audits covered Fleet drift and current official runtime surfaces.
- Inline exception: the owner performs the tightly coupled model→collector→route→render→test edit because registered stage workers are unavailable and the bounded read audits already supplied independent plan evidence.
- Reduced Fleet parity: native subagents/background sessions/non-interactive workers are distinct runtime surfaces. Compensation is focused fixtures, full Fleet regression, mirror parity, wrapper syntax/compile checks, projection checks, and portable guards.

## Stage graph

1. Plan/check — reconcile v14 contract against current Fleet and refute schema/identity assumptions.
2. Execute — carry optional `unit` through wrappers, jobs/process collector, model, route projections, and compact UI labels; retain legacy fallbacks; correct memory journal documentation.
3. Test — focused unit/route/dispatch/render/memory/subagent/v20 checks, full suite, mirror/projection and portable guards.
4. Report — record evidence, close spec dev status, commit source branch only after PASS.

## Implementation boundaries

- Never infer `unit` from native subagent type or legacy `worker_role`.
- Preserve the current Fleet stage layout and ordering unchanged in this cycle. The user prefers complete stage visibility but rejected a quick wrapping treatment; no stage-layout redesign is authorized here.
- Keep route schema version 2 and dispatch contract version 3; topology registry alone is schema version 3.
- Preserve v20 attempt/route/node terminal correlation.
- Preserve old jobs rows and route records when additive unit fields are absent.
- Keep `/proc` + jobs.log as Fleet backbone; `claude agents --json` remains a documented residual extension, not claimed parity.
- Do not edit runtime homes, config, credentials, logs, caches, or user-owned stage-dispatch artifacts.

## Planned verification

- Focused Fleet tests: dispatch, route/process view, F-15 rows, memory, subagents, v20 contract, mirror parity.
- Full `tools/fleet/tests` suite.
- `py_compile`, wrapper shell/python syntax, representative Fleet JSON/once smoke where safe.
- Canonical↔Claude mirror parity and runtime projection check.
- Relevant adaptation-boundary/portable guard checks.

## Plan check (refute by default)

- Refuted: route schema became v3. It remains v2; the topology registry is v3.
- Refuted: unit replaces assigned contract or worker type. It is an independent optional execution-unit axis.
- Refuted: native subagent agent type can supply unit. Runtime identities and portable units are intentionally separate.
- Refuted: memory commits require a Fleet schema migration. The journal already emits `cwd`; only stale documentation needs correction.
- Refuted after user UI feedback: treat the long horizontal stage observation as authorization for a quick UI patch. The original Fleet semantic-migration scope remains unchanged.
- Known baseline red: canonical/Claude mirror differs by one terminology-only render comment. The implementation must regenerate/synchronize the mirror and eliminate it.
