# Verification — round 2 (depth-0 fix-forward, 2026-07-17)

- Basis: round-1 codex audit (`test_logs/`) — 3 confirmed gate defects; fix commit `764934c6`.
- All commands ran inside `/home/Uihyeop/agent_setting-wt/evidence-autobind`, `AGENT_DISPATCH_JOBS` unset.

## Defect fixes verified (adversarial recheck, 14/14 PASS)

1. Failed probe (rc 69) with identity-matching `supported` JSON is rejected in all
   three wrappers; a successful probe still binds `supported`; checked
   `unsupported` JSON from rc 69 still binds and fails closed (no over-tightening).
2. Explicit `--nested-eligibility unknown` is tracked as explicit (None-sentinel
   parser default + provenance), never overwritten; the probe is not invoked.
3. `bind_dispatch_evidence` always compares `--eligibility-failure-class`;
   explicit `forged` vs empty record raises `dispatch-evidence-explicit-conflict`;
   the flag is omitted from output only when both sides are empty.

## Regression

dispatch_node (17 OK) · dispatch_contract · stage_dispatch_fallback ·
nested_dispatch_eligibility · dispatch-route PASS · sd15 ×3 PASS · sd45 ×3 (9 OK each) ·
boundary guard clean except two baseline `mem.py` findings (pre-existing).
Boundary follow-ups landed: `dispatch_node.test.py` classified deferred (codex/opencode)
and projected for claude.

## Verdict

code-test gate: **PASS** — acceptance g10 drill runs at depth-0 integration below.
