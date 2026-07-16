# Recursive Codex headless smoke

verdict: **PASS**
date: 2026-07-16

## Topology

`root -> Codex depth-1 headless owner -> Codex depth-2 headless code-plan stage`

- Owner slug/attempt: `final-recursive-owner-2` /
  `att-bc421db7284945adac823fe5367b1509`.
- Stage slug/attempt: `final-recursive-plan-2` /
  `att-09f636ba2c930e713bb539651d339a62ef4e60802f30d631`.
- Route/node: `rt-3cf2d7280803a89b` / `plan`.

## Result

The depth-1 owner invoked `stage-dispatch-fallback.py --start` and returned:

```text
check=ok
selected_hop=same-harness-headless
fallback_ordinal=1
child_harness=codex
launch_authority=conductor
broker_lifecycle=retired
attempt_trace=...:direct:exit-0:attempt-att-09f636...|...:watchdog-terminal
```

The stage launched with a unique exact-attempt log, route-bound `.dispatch`
write access, and no nested network. Its heartbeat advanced through launch,
analysis, tool, and terminal phases; final sequence was `4`. Both rows were
reconciled and the selected registry had zero open rows. No broker process,
request, spool, daemon, or broker lifecycle start occurred.

## Fixture correction and finding

The first invocation used a registry under `.tmp-*`, outside the owner's
writable scope, and correctly failed with exit `73`. This was a smoke-fixture
path error, not a source failure; the registry was moved to the canonical
`.dispatch` scope and the exact same recursive path passed.

The passing run recorded stage PID `437`, which was local to the owner's PID
namespace. Root reconciliation initially saw that numeric PID as missing/reused.
The follow-up fix now writes `pid_scope=namespace-local`; root Fleet/liveness/
reconciliation use only a matching fresh exact heartbeat, classify terminal
heartbeat as `done`, and never probe an unrelated host PID. Deterministic tests
for fresh, terminal, and stale namespace heartbeat cases all pass.
