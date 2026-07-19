# Implementation log

## Result

Implemented passive Codex native-subagent enrichment in the existing
`Session.subagents` model. No new render or JSON schema was introduced.

Changed source surfaces (canonical and required Claude mirror are byte-equal):

- `tools/fleet/collectors/codex.py`
- `adapters/claude/tools/fleet/collectors/codex.py`
- `tools/fleet/model.py`
- `adapters/claude/tools/fleet/model.py`
- `tools/fleet/tests/test_f29_subagents.py`
- `adapters/claude/tools/fleet/tests/test_f29_subagents.py`

## Runtime evidence and decisions

- Codex 0.144.6 exposes exact parent/child links in
  `thread_spawn_edges(parent_thread_id, child_thread_id, status)` and child
  metadata in `threads`.
- A fresh native `spawn_agent` produced parent `019f7b58-…` and child
  `019f7b69-…`; the edge and child `source` JSON agree on the exact parent.
- A runtime census found 67 open edges: 47 ended in `task_complete`, 13 in
  `turn_aborted`, and only 7 in `task_started`; 6 of those starts were stale.
  Consequently edge-open, parent PID, and open file ownership cannot prove
  active work.
- Open-edge rollouts are scanned backward through at most 1 MiB. Lifecycle
  events must have a valid `turn_id`; a terminal must pair with the immediately
  preceding start for that turn. A fresh unmatched start (within the shared
  60-second work window) is active. Stale, malformed, mismatched, or unreadable
  evidence is omitted rather than guessed.
- `agent_role` is preferred as type. When absent, the final `agent_path`
  component supplies the native configured agent identity; nickname is ignored.
- Runtime home is derived from the already-attributed parent rollout path so a
  session created under a dispatched/nested `CODEX_HOME` consults its owning DB.

## Safety and fallback behavior

- SQLite opens with URI `mode=ro`, then `PRAGMA query_only=ON`.
- Fleet never writes state DBs, WAL/SHM, rollouts, config, or caches.
- Exact edge, exact source-JSON parent, `thread_source=subagent`, one parent per
  child, and known status are required. An open edge additionally requires a
  readable child rollout. Any
  ambiguity or schema absence omits enrichment without altering top-level
  sessions.
- A short DB/WAL/SHM-stamp cache avoids repeated state scans while remaining
  WAL-aware. Direct `immutable=1` is intentionally not used because it missed
  an uncheckpointed live edge during review.

## Dispatch and guard evidence

- Route: `rt-095d82a8da1ac698`, dispatch contract v3.
- Registered Codex plan stage failed at sandbox bootstrap because the nested
  worker could not create the spec-grounding marker on a read-only mount.
- Registered Claude fallback was synchronously polled, reached two quiet
  watchdog windows, and was closed `dead-no-progress` (`Execution error`).
- The checked fallback chain then selected inline for plan/execute and is
  checked again for test/report; all stage bodies remain durable artifacts.
- Native reviewer `/root/codex_status_semantics_review` established the
  fail-closed lifecycle policy and required fixtures. Native
  `/root/fleet_live_probe` then found no obvious bug in the resulting parser.
- Final native reviewer `/root/fleet_final_review` inspected the realized diff,
  reran all 681 Fleet tests plus focused checks, and reported no findings.
- The trusted main session recorded the core-first reads and all adapter write
  preflights in the isolated worktree before the final edits.
