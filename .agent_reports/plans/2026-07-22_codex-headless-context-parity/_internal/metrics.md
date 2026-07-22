# Execution topology metrics

- date: 2026-07-22
- capability: autopilot-code
- intensity: standard
- dispatch_depth: 1
- worker_type: owner
- execution: inline capability pipeline in the registered depth-1 owner
- exception: runtime-unavailable
- reason: This self-hosting change repairs the Codex parent wait/liveness seam
  that currently leaves a terminal `PASS` child registry row open until a
  depth-0 caller manually reads the handoff and writes completion. Dispatching
  depth-2 stages would depend on the broken lifecycle being changed and could
  not be closed safely by this owner. Per assignment, no child was dispatched.
- assurance: `qa-policy thorough code` requires
  `plan-check:selected-independent-pass:final-verify`; independent child QA is
  unavailable for the same runtime reason, so implementation review is inline
  and must be reported as such rather than claimed as delegated.
