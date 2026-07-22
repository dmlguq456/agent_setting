---
status: active
created: 2026-07-22
---

# Fleet memory sync-event implementation checklist

## Scope locks

- [x] Confirm HEAD is `e8938809d87e54474f5e7242a2552598c2636a0a` before the first source edit; if it moved, stop and return to the owner rather than silently rebasing the plan.
- [x] Confirm the sealed route still carries satisfied `tracked_gate_evidence.spec_read` and the completed spec-owner report; these are the authoritative prerequisites.
- [x] Immediately before the first source edit, run the plan's exact-text gate against `/home/Uihyeop/agent_setting/.agent_reports/spec/prd.md` (D-37 v22) and `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md` (F-19/F-35f v15 text); fail closed on drift.
- [x] Do not require, create, stage, or commit a linked-worktree copy of the canonical artifact-root spec edits.
- [x] Run the required write preflight before every edited file.
- [x] Edit only `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh`; if the producer-to-Fleet acceptance test demonstrates a real consumer gap, capture evidence and obtain owner scope approval before adding the collector.
- [x] Keep `tools/fleet/collectors/memory.py`, DB schema, `sync()` sequencing, source keys, DB `cwd_origin`, journal rotation, and all specs unchanged.
- [x] Never invoke migrate/sync against the real memory store or journal; every test sets isolated `MEM_STORE`, `MEM_PROJECTS`, `MEM_PROFILE`, and `MEM_WRITE_EVENTS`.
- [x] Route every acceptance `sync` call through the fenced helper with explicit `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`; forbid raw/unwrapped `mem.py sync` calls.
- [x] Give every sync acceptance scenario a newly allocated store that was empty at creation and is proven non-Git before seeding; never reuse another scenario's store.
- [x] Do not synthesize/replay/backfill historical events.
- [x] Do not commit, push, merge, rebase, reset, or clean this linked worktree; integration belongs to the depth-1 owner.

## Shared event plumbing — `tools/memory/mem.py`

- [x] Add a private unset sentinel for event cwd.
- [x] Add a pure source-cwd decoder: encoded or existing absolute input -> resolved absolute path string; invalid/missing/relative input -> `None`.
- [x] Extend `_append_write_event()` with a trailing cwd override.
- [x] Verify default/unset cwd still emits `MEM_CWD` first, then process cwd.
- [x] Verify explicit path ignores ambient/process cwd.
- [x] Verify explicit `None` omits the `cwd` key entirely.
- [x] Preserve `MEM_SID`, snippet truncation/sanitation, timestamp, JSON shape, 256KB/500-line rotation, and fail-open behavior.
- [x] Extend `write_record()` with trailing `journal_insert_only`, `journal_actor`, and `journal_cwd` options (or exact equivalents).
- [x] Gate source upsert and body-dedup journal calls only when insert-only mode is enabled.
- [x] Keep the INSERT journal call enabled in insert-only mode.
- [x] Leave defaults compatible so manual add/note still journal upsert, dedup reinforcement, and INSERT with ambient actor/cwd behavior.

## Migration source wiring — `tools/memory/mem.py`

- [x] Auto-memory: pass `action=add`, literal `actor=sync`, insert-only mode, and decoded `mp.parent.parent.name` logical cwd.
- [x] Auto-memory decode failure: pass explicit missing cwd, not fallback.
- [x] Post-it: pass resolved `pi.parent.parent` repo root as event cwd; preserve encoded source namespace and canonical DB key.
- [x] Global profile: pass explicit missing cwd.
- [x] Legacy frontmatter: pass only a valid decoded/existing absolute cwd.
- [x] Legacy missing/invalid cwd: pass explicit missing cwd.
- [x] All four source loops preserve `existing_src` skip behavior.
- [x] No caller uses `_write_actor(default="sync")`; every absorption passes literal `sync` so `MEM_ACTOR` and `MEM_DISTILL` cannot override it.
- [x] Grep all `write_record(` and `_append_write_event(` call sites after editing and verify no positional caller/signature drift.

## Focused acceptance tests — `tools/memory/mem_cluster_j.test.sh`

- [x] General caller with `MEM_CWD` retains env override.
- [x] General caller without `MEM_CWD` retains process-cwd fallback.
- [x] Manual add/note source-upsert and body-dedup journal behavior remains enabled.
- [x] Hostile-env auto-memory migration emits exactly one event and one DB row.
- [x] Hostile-env event is exactly `action=add`, `actor=sync`, decoded absolute source cwd; it ignores `MEM_ACTOR=curator`, `MEM_DISTILL=1`, `MEM_CWD=/wrong/repo`, and wrong process cwd.
- [x] Registered post-it fixture uses an exact resolved repo root whose basename is `agent-note` and registers `<repo>/.agent_reports/post-it.md` in the isolated store.
- [x] Registered post-it event resolves by its DB source to exactly one raw journal row with `action=add`, literal `actor=sync`, and `cwd` exactly equal to that repo root.
- [x] The actual registered-post-it event groups in Fleet `by_repo["agent-note"]` with the same `action=add` and `actor=sync`.
- [x] A separate second `migrate --apply` leaves DB row/strength/source snapshots and journal line count unchanged; do not substitute `sync` for this idempotency assertion.
- [x] The fenced `sync` integration call runs only after repeat-migrate proof and leaves DB rows/journal unchanged while rebuilding index mirrors and exporting the isolated dump.
- [x] Immediately before and after every fenced sync, compare content-sensitive snapshots of the real runtime store, profile, write journal, dump, plus worktree status/unstaged diff/staged diff; require exact equality.
- [x] Duplicate identical post-it bullets produce one INSERT event total; same-run source upsert produces none.
- [x] Distinct post-it source with normalized duplicate body reinforces strength but produces no absorption event.
- [x] Pre-existing exact source plus journal sentinel produces no event on the first post-change migrate (prospective-only/no backfill).
- [x] Registered post-it event cwd is the repo root, not ambient/process cwd.
- [x] Auto-memory decode failure, global profile, legacy missing cwd, and legacy invalid/nonexistent cwd events are resolved by record/source and their raw JSON objects have no `cwd` key (not `null`, empty, ambient, or process fallback).
- [x] Valid encoded and absolute legacy cwd values emit the exact resolved logical cwd.
- [x] `mem log --json --actor sync` parses, reports the exact absorption-event ID set, returns only `action=add`/`actor=sync`, and excludes a mixed-in manual event.
- [x] All fixtures stay under temporary roots and the trap removes them.

## Consumer boundary

- [x] First run the real producer-row -> `fleet.collectors.memory.collect()` acceptance test.
- [x] If `by_repo["agent-note"]` passes, leave `tools/fleet/collectors/memory.py` unchanged.
- [ ] If it fails, capture the exact JSON row, `collect()` result, and traceback/assertion; distinguish malformed producer output from a true consumer gap.
- [ ] Do not edit the consumer on speculation. A real consumer change requires owner direction because it expands the approved minimal scope and Claude Fleet mirror surface.

## Verification commands

- [x] `python3 tools/memory/mem.py --help >/dev/null`
- [ ] `bash tools/memory/distill.test.sh`
- [x] `bash tools/memory/empty-store-guard.test.sh`
- [x] `bash tools/memory/inject.test.sh`
- [x] `bash tools/memory/mem_cluster_e.test.sh`
- [x] `bash tools/memory/mem_cluster_e_gamma.test.sh`
- [x] `bash tools/memory/mem_cluster_j.test.sh`
- [x] `bash tools/memory/mem_repairs_v15.test.sh`
- [x] `bash tools/memory/mem_retrieval_v14.test.sh`
- [x] `bash tools/memory/pending_drain.test.sh`
- [x] `bash tools/memory/retrieval-eval.test.sh`
- [x] Confirm all ten canonical `tools/memory/*.test.sh` suites above ran; no suite is excluded. If a runtime/tool contract is unavailable, name the suite, command, exit status, and contract explicitly; a test failure is not an exclusion.
- [ ] `bash tools/memory/distill.test.sh` — exit 1, `PASS=35 FAIL=2`; both failures reproduced with zero diff on `tools/memory/distill.test.sh`, `hooks/mem-distill-dispatch.sh`, and `hooks/mem-turn-nudge.test.sh` (outside the approved edit scope) — see `dev_logs/execute-fix1.md` disposition. Left unchecked pending owner disposition per the plan's gate text; not self-certified as complete.
- [x] `(cd tools && PYTHONPATH=.. python3 -m unittest fleet.tests.test_f19_memory -v)` — 26/26.
- [x] `PYTHONPATH=. python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py' -v` — 744/744; repository-root import path.
- [x] `test "$(readlink adapters/claude/tools/memory/mem.py)" = "../../../../tools/memory/mem.py"`
- [x] `AGENT_HOME="$PWD" adapters/codex/tools/memory/mem.py --help >/dev/null`
- [x] `AGENT_HOME="$PWD" adapters/opencode/tools/memory/mem.py --help >/dev/null`
- [x] `./tools/check-adaptation-boundary.sh` — pass; emits documented 126-reference warning.
- [x] Run the plan's executable `git status --porcelain=v1 -z` parser and prove the only changed worktree paths are `tools/memory/mem.py` and `tools/memory/mem_cluster_j.test.sh`.
- [ ] If a collector change was evidence-backed and owner-approved, update the recorded approved set before that edit and include the approved collector path in the diff check; otherwise any collector diff fails.
- [x] `git diff --check`

## Evidence and completion gate

- [x] Record every changed file, command, exit code, assertion count, and warning in the canonical stage artifact.
- [x] Record the canonical spec-gate output and the route's satisfied spec-read/spec-owner prerequisites; do not claim a linked-worktree spec commit.
- [x] Record a focused `git diff` showing only the approved source/test files (plus canonical stage artifacts outside the worktree).
- [x] Record every sync command line with `MEM_DUMP_COMMIT=0 MEM_DUMP_PUSH=0`, the fresh/non-Git store proof, and the matching before/after real-store/profile/journal/dump/worktree snapshot digests.
- [x] Confirm no real `write-events.jsonl`, `memory.db`, `dump.jsonl`, user profile, runtime configuration, worktree diff, index, commit, or remote changed during sync acceptance.
- [x] Confirm no journal backfill/rewrite command was run.
- [x] Confirm `git status --short` has no unrelated worktree changes.
- [x] Pass the route's independent `plan-check` and final verification gates; do not self-label inline review as independent QA.
- [x] Hand the uncommitted diff and evidence to the depth-1 owner for integration, commit, push, and eventual cleanup.
