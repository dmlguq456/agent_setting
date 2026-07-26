# Supervised owner → code-plan live smoke

- Date: 2026-07-26 Asia/Seoul
- Registry: `jobs.log` in this directory
- Owner attempt: `att-3fedfb87bf9942c7a8c2c701c02509af`
- Child attempt: `att-ac2d63c649184f38a812b684771a8932`
- Scope: one foreground-scoped App Server supervised Codex owner and one
  foreground-scoped Codex `code-plan` child; no source/spec/Git writes.

## Required observations

- Owner: `registered=1`, `started=1`, `child_spawned=1`, terminal verdict
  `PASS`, handoff source `exact-turn-completed`.
- Child: `registered=1`, `started=1`, `child_spawned=1`,
  `parent_liveness_source=supervisor-lease`, `nested_eligibility=supported`,
  `eligibility_probe=internal`, `launch_claimed=1`, `launch_started=1`.
- Runtime delivery: one `dispatch.supervisor.parked` event and one
  `dispatch.supervisor.resumed` event with `state=ready`; the exact child was
  then harvested and closed `note=harvest-complete`.
- Liveness: `open 0 ; alive 0 ; suspect/dead 0`.
- Exact harvest: both owner and child matched once, with valid
  `exact-turn-completed` handoffs and `PASS` verdicts.
- Cleanup: owner lease, supervisor phase state, owner PID, and namespace-local
  child PID were all absent after completion.

This proves the previously failing path from an App Server tool PID namespace:
the child could not use the owner's outer PID as authoritative local evidence,
bound the same exact owner through the held nonce-sealed lease, passed the
internal Codex auth check, launched once, completed, resumed, and harvested.
