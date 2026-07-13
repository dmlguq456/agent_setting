# Fleet Codex live-attribution hotfix — 2026-07-13

- Changed canonical `tools/fleet` only, then synchronized the byte-identical Claude mirror.
- Codex rollouts now resolve per PID through `/proc/<pid>/fd`; root/user metadata wins over an open `source=subagent` rollout.  Idle fallback assigns only one uniquely time-compatible, unclaimed rollout; ambiguous sessions remain unknown.
- Renderer suppresses a repeated child tree for a duplicate `session_id`.
- Verification: focused F-18 18/18; canonical Fleet 165/165; Claude mirror Fleet 159/159 with 6 existing statusline-dependent skips; canonical mirror parity 1/1.
- Live `python3 tools/fleet/fleet.py --once`: `dispatch-routing-policy` dispatch tree count changed 2 → 1 beneath the two interactive `agent_setting` Codex rows; no detached/headless top-level Codex row appeared.
