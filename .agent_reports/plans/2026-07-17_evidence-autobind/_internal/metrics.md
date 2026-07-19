
## depth-0 fix-forward (round 2, 2026-07-17)

- inline reason (SD-17): execute node pinned to source_commit 5972a61d with HEAD moved;
  the three fixes were micro-edits fully specified by the code-test audit. Dispatch
  overhead clearly exceeds the stage — §5.10 inline exception. Commit 764934c6.
- adversarial recheck: 14/14 PASS (rc69-supported rejected in 3 wrappers; successful
  probe still binds; rc69 checked-unsupported retained; explicit unknown preserved ×3;
  dispatch-node forged failure-class fails loud; empty/empty omitted from output).
- regression: dispatch_node 17 OK, dispatch_contract OK, stage_dispatch_fallback OK,
  nested_dispatch_eligibility OK, dispatch-route PASS, sd15 ×3 PASS, sd45 ×3 (9 OK each),
  boundary guard clean except 2 baseline mem.py findings. AGENT_DISPATCH_JOBS unset.
- core-first: stale SD-48 "follow-up" sentence replaced with the implemented contract
  before adapter edits.
