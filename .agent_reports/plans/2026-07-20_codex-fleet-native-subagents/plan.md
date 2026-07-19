# Plan — Codex native subagents in Fleet

spec-significance: within-spec — this closes the explicit F-29 Codex runtime-probe gap without changing the shared `Session.subagents` or render contract.

## Runtime grounding

- Official Codex manual (current local manual cache, source page `agent-configuration/subagents.md`): subagents run in agent threads; CLI exposes them through `/agent`; clients expose Active and Done collections; custom agents carry a configured agent identity; parent orchestration owns spawn/wait/close.
- Official Claude reference is parity context only. Claude's transcript collector remains a sibling implementation.
- Live Codex 0.144.6 read-only probe found `state_5.sqlite.thread_spawn_edges(parent_thread_id, child_thread_id, status)` and child metadata in `threads(agent_role, agent_path, agent_nickname, thread_source, created_at[_ms], updated_at[_ms], rollout_path)`.
- A native `spawn_agent` probe created an exact row from parent thread `019f7b58-…` to child `019f7b69-…` with status `open`; the child row reported `thread_source=subagent`, `agent_path=/root/runtime_probe_review`, and nickname `Ohm`. The child rollout repeated the same `parent_thread_id`, `agent_path`, and nickname in `session_meta`.

## Implementation

1. Add a tolerant, stamp-cached Codex state-DB subagent index in `tools/fleet/collectors/codex.py`.
   - Read the newest versioned DB through SQLite URI `mode=ro` plus `PRAGMA query_only=ON`.
   - Join exact `thread_spawn_edges.child_thread_id` to `threads.id`.
   - Require one unambiguous parent per child; omit ambiguous/malformed children.
   - Treat a closed edge as done. For an open edge, validate physical-order
     `task_started`/`task_complete`/`turn_aborted` events and matching `turn_id`.
     A fresh unmatched start is active, a matching terminal is done, and stale,
     malformed, or mismatched lifecycle is omitted.
   - Resolve type from `agent_role`, falling back to the final `agent_path`
     component used by native agent threads. Never use nickname as type.
   - Return `None` when the source/schema is unavailable, `[]` when the source is confirmed but the parent has no children.
2. Attach the indexed children only after Codex enrichment has already established an exact `Session.session_id`; never create, suppress, or reclassify sessions.
3. Apply the same collector change to `adapters/claude/tools/fleet/collectors/codex.py` to preserve the repository's canonical↔Claude byte-parity rule.
4. Extend `tools/fleet/tests/test_f29_subagents.py` and its mirror with Codex fixtures for exact parent linkage, role/path type, matching completion/abort, multi-turn ordering, stale starts, partial JSON, WAL-only edges, ambiguity, malformed/absent schema, and enrichment-only behavior. Existing Claude/OpenCode and render/JSON tests remain the regression contract.

## Verification

- Focused: `python3 -m unittest tools.fleet.tests.test_f29_subagents`
- Full Fleet: `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`
- Mirror: byte compare `tools/fleet/` against `adapters/claude/tools/fleet/` for changed files and run mirror-parity tests.
- Repository: `python3 tools/build-manifest.py --check`; `tools/check-adaptation-boundary.sh`.
- Live smoke: snapshot runtime DB/WAL/SHM/config/rollout metadata, call only the new read-only collector against the observed native edge, confirm parent/type/status, then compare metadata to prove Fleet made no runtime mutation.

## Pipeline exception record

The registered Codex planner was blocked by sandbox bootstrap (`bwrap` could not create `.spec-grounding/.git` on the read-only mount). The checked Claude fallback reached two no-progress watchdog windows and was closed `dead-no-progress`. The checked route then skipped native fallback for missing child-proof and selected its recorded inline fallback. This plan is the durable inline fallback body; execute, test, and report each retain a checked dispatch-chain selection and route-bound completion marker.
