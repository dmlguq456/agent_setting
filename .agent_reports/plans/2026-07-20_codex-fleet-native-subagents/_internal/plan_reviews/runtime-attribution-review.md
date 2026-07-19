# Risk-focused plan review

Verdict: proceed with a narrow state-DB enrichment.

Primary risks and controls:

- Wrong parent: accept only the explicit `thread_spawn_edges` relation; if one child appears under multiple parents, omit it everywhere.
- False active/done: use closed edge status plus matching
  `task_started`/`task_complete`/`turn_aborted` and `turn_id`. The live census
  proved that 60 of 67 open edges were already terminal. A fresh unmatched
  start is active; stale or ambiguous evidence is omitted.
- Wrong agent type: prefer `threads.agent_role`; if absent, use the final
  `agent_path` component exposed by native agent threads. Never use nickname.
- Runtime mutation: open the DB read-only, set query-only, never issue schema/PRAGMA mutation commands, and compare DB/WAL/SHM/config/rollout metadata around the live smoke.
- Session topology regression: attach only after exact session-id enrichment and leave classification/procscan/render code unchanged.
- WAL drift: read with `mode=ro` plus `query_only` and invalidate the short
  cache on DB/WAL/SHM stamps. `immutable=1` is forbidden for the live original
  because it can miss uncheckpointed edges.
- Schema drift: missing tables/columns or SQLite errors return `None`, preserving the honest gap and existing session rows.

Required assurance from `qa-policy standard code`: native reviewer
`/root/codex_status_semantics_review` supplied the deep runtime-semantics pass;
`/root/fleet_live_probe` inspected the parser, and
`/root/fleet_final_review` reported no findings on the final realized diff.
